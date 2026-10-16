/*
 * V2NATIVE-0668: synthetic, native controller-authenticated prepaid journal.
 * LAB-ONLY, never installed in OpenWrt rootfs, no live payment endpoint.
 * Build: cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY
 *        tools/v060_journal_authority_native.c -lcrypto -o v2-native-fixture
 * Usage: v2-native-fixture /tmp/blaze-v2-native-XXXXXX
 *        CONTROLLER SEQ EVENT OP SUBJECT TARGET UNITS NOW HMAC_SHA256
 * Requires private marker, private key registry, private ledger.
 * This does not implement production v1 migration, target power-loss proof,
 * key rotation, or encrypted backup. No flags can enable customer operation.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <openssl/crypto.h>
#include <openssl/hmac.h>
#include <openssl/sha.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#ifndef BLAZE_FIXTURE_ONLY
#error "Native authority must not be built without LAB-ONLY fixture guard"
#endif
#define ROOT_PREFIX "/tmp/blaze-v2-native-"
#define MAX_LEDGER 2097152
#define MAX_BANK 512
#define MAX_LEASE 512
#define MAX_CTL 128
#define MAX_RECEIPT 1024
struct item { char name[33]; unsigned long long value; };
struct receipt {
    char ctl[33], event[48], digest[65], result[32];
    unsigned long long seq;
};
static struct item bank[MAX_BANK], lease[MAX_LEASE], ctl[MAX_CTL];
static struct receipt receipts[MAX_RECEIPT];
static int nb=0,nl=0,nc=0,nr=0,dirfd=-1,lockfd=-1;
static char next_name[64];
static int renamed=0;
static void die(const char *why) {
    fprintf(stderr,"V2NATIVE-0668 REJECT: %s (no ACK)\n",why);
    exit(8);
}
static int valid_id(const char *p) {
    size_t i,n=p?strlen(p):0;
    if(n==0 || n>32 || !((p[0]>='A'&&p[0]<='Z') ||
                        (p[0]>='a'&&p[0]<='z'))) return 0;
    for(i=1;i<n;i++) if(!((p[i]>='A'&&p[i]<='Z') ||
      (p[i]>='a'&&p[i]<='z') || (p[i]>='0'&&p[i]<='9') ||
       p[i]=='_' || p[i]=='-' || p[i]=='.')) return 0;
    return 1;
}
static int hex64(const char *s) {
    size_t i;
    if (!s || strlen(s)!=64) return 0;
    for(i=0;i<64;i++) if(!((s[i]>='0'&&s[i]<='9') ||
       (s[i]>='a'&&s[i]<='f'))) return 0;
    return 1;
}
static void unhex(const char *s,unsigned char *b,size_t n) {
    size_t i;
    for(i=0;i<n;i++) {
        char h=s[2*i],l=s[2*i+1];
        b[i]=(unsigned char)(((h<='9'?h-'0':h-'a'+10)<<4) |
                             (l<='9'?l-'0':l-'a'+10));
    }
}
static void hexout(const unsigned char *b,size_t n,char *hex) {
    static const char chars[]="0123456789abcdef";
    size_t i;
    for(i=0;i<n;i++){hex[2*i]=chars[b[i]>>4];hex[2*i+1]=chars[b[i]&15];}
    hex[2*n]=0;
}
static int parse_uint(const char *s,unsigned long long max,unsigned long long *out) {
    size_t i,n=s?strlen(s):0;
    unsigned long long v=0;
    if(n<1 || n>15 || (n>1&&s[0]=='0'))return 0;
    for(i=0;i<n;i++){
        if(s[i]<'0'||s[i]>'9')return 0;
        if(v>(max-(unsigned)(s[i]-'0'))/10)return 0;
        v=v*10+(unsigned)(s[i]-'0');
    }
    *out=v;return 1;
}
static int parts(char *line,char **v,int limit) {
    int n=0;char *p=line;
    if(!*p)return 0;
    v[n++]=p;
    for(;*p;p++)if(*p=='\t'){
        *p=0;if(n==limit)return -1;
        v[n++]=p+1;
    }
    return n;
}
static int private_fd(int fd,mode_t mode) {
    struct stat st;
    return fstat(fd,&st)==0 && S_ISREG(st.st_mode) &&
      st.st_nlink==1 && st.st_uid==geteuid() &&
      (st.st_mode&0777)==mode;
}
static void read_exact(int fd,char *buf,size_t n) {
    size_t pos=0;
    while(pos<n){
        ssize_t got=read(fd,buf+pos,n-pos);
        if(got<0&&errno==EINTR)continue;
        if(got<=0)die("short or failed protected read");
        pos+=(size_t)got;
    }
}
static char *readfile(const char *name,size_t cap,size_t *n) {
    struct stat st;
    int fd=openat(dirfd,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    char *buf;
    if(fd<0 || !private_fd(fd,0600) || fstat(fd,&st)!=0 ||
       st.st_size<0 || (unsigned long long)st.st_size>cap)
       die("missing/non-private protected file");
    *n=(size_t)st.st_size;
    buf=malloc(*n+1);if(!buf)die("out of memory");
    read_exact(fd,buf,*n);
    buf[*n]=0;
    { struct stat end;
      if(fstat(fd,&end)!=0 || end.st_size!=st.st_size ||
         end.st_mtim.tv_sec!=st.st_mtim.tv_sec ||
         end.st_mtim.tv_nsec!=st.st_mtim.tv_nsec ||
         end.st_ctim.tv_sec!=st.st_ctim.tv_sec ||
         end.st_ctim.tv_nsec!=st.st_ctim.tv_nsec)
        die("source changed during read");
    }
    if(close(fd)!=0)die("file read close failure");
    if(memchr(buf,0,*n))die("binary file content rejected");
    return buf;
}
static struct item *find(struct item *arr,int n,const char *id) {
    int i;for(i=0;i<n;i++)if(strcmp(arr[i].name,id)==0)return &arr[i];
    return NULL;
}
static void parseledger(char *s,size_t len) {
    char *p=s,*end=s+len,*v[7];size_t count=0;
    unsigned char hash[32];char expected[65];
    size_t i,footer_start=0;
    if(!len || s[len-1]!='\n')die("ledger missing final newline");
    for(i=0;i+1<len;i++)if(s[i]=='\n')footer_start=i+1;
    if(len-footer_start!=67 || s[footer_start]!='H' ||
       s[footer_start+1]!='\t')die("missing final integrity footer");
    {char footer_hex[65];memcpy(footer_hex,s+footer_start+2,64);
     footer_hex[64]=0;if(!hex64(footer_hex))die("malformed footer hash");
     SHA256((const unsigned char*)s,footer_start,hash);
     hexout(hash,32,expected);
     if(CRYPTO_memcmp(expected,footer_hex,64)!=0)
       die("SHA-256 integrity footer mismatch");
    }
    while(p<end){
        char *newline=memchr(p,'\n',(size_t)(end-p));
        int n;
        if(!newline)die("incomplete record");
        *newline=0;count++;
        n=parts(p,v,7);
        if(count==1){if(n!=2||strcmp(v[0],"V")||strcmp(v[1],"2"))
          die("unsupported ledger version");
        } else if(n==2 && strcmp(v[0],"H")==0){
            if(newline!=end-1 || !hex64(v[1]))die("invalid integrity footer");
            return;
        } else if(n==3 && !strcmp(v[0],"A")){
            unsigned long long z;
            if(!valid_id(v[1])||!parse_uint(v[2],2000000000ULL,&z) ||
               nb>=MAX_BANK||find(bank,nb,v[1]))die("malformed/duplicate bank");
            strcpy(bank[nb].name,v[1]);bank[nb++].value=z;
        } else if(n==3 && !strcmp(v[0],"L")){
            unsigned long long z;
            if(!valid_id(v[1])||!parse_uint(v[2],2000000000ULL,&z) ||
               nl>=MAX_LEASE||find(lease,nl,v[1]))die("malformed/duplicate lease");
            strcpy(lease[nl].name,v[1]);lease[nl++].value=z;
        } else if(n==3 && !strcmp(v[0],"C")){
            unsigned long long z;
            if(!valid_id(v[1])||!parse_uint(v[2],100000000ULL,&z) ||
               nc>=MAX_CTL||find(ctl,nc,v[1]))die("malformed/duplicate controller");
            strcpy(ctl[nc].name,v[1]);ctl[nc++].value=z;
        } else if(n==6 && !strcmp(v[0],"R")){
            unsigned long long z,res;
            struct receipt *a;
            if(nr>=MAX_RECEIPT||!valid_id(v[1])||
               !parse_uint(v[2],100000000ULL,&z)||z==0||
               strlen(v[3])>=sizeof(receipts[0].event)||
               !hex64(v[4])||!parse_uint(v[5],2000000000ULL,&res))
                die("malformed receipt");
            a=&receipts[nr++];strcpy(a->ctl,v[1]);a->seq=z;
            strcpy(a->event,v[3]);strcpy(a->digest,v[4]);
            strcpy(a->result,v[5]);
            {char eid[64];snprintf(eid,sizeof(eid),"%s:%llu",v[1],z);
             if(strcmp(eid,a->event))die("receipt event/sequence mismatch");}
        } else die("malformed journal record");
        p=newline+1;
    }
    die("missing ledger integrity footer");
}
static void validate_receipts(void) {
    int i,j;
    for(i=0;i<nr;i++){
        struct receipt *a=&receipts[i];
        struct item *x=find(ctl,nc,a->ctl);
        if(!x || a->seq>x->value ||
          (x->value>=8 && a->seq<=x->value-8))
           die("receipt without valid retained controller floor");
        for(j=0;j<i;j++)if(!strcmp(receipts[j].ctl,a->ctl) &&
                            receipts[j].seq==a->seq)
           die("duplicate controller sequence receipt");
    }
}
static void getkey(const char *wanted,unsigned char key[32]) {
    size_t n;char *data=readfile("controller-keys.tsv",16384,&n);
    char *p=data,*e=data+n;int seen=0,count=0,i,j,nonzero;
    char ids[MAX_CTL][33];
    unsigned char keys[MAX_CTL][32],decoded[32];
    while(p<e){
        char *nl=memchr(p,'\n',(size_t)(e-p)),*v[3];
        if(!nl)die("incomplete controller registry row");
        *nl=0;
        if(parts(p,v,3)!=2||!valid_id(v[0])||!hex64(v[1])||
           count>=MAX_CTL)
            die("invalid controller key registry");
        unhex(v[1],decoded,sizeof(decoded));
        nonzero=0;
        for(j=0;j<32;j++)if(decoded[j])nonzero=1;
        if(!nonzero)die("zero controller secret rejected");
        for(i=0;i<count;i++){
            if(!strcmp(ids[i],v[0]))
                die("duplicate controller identity");
            if(CRYPTO_memcmp(keys[i],decoded,sizeof(decoded))==0)
                die("duplicate controller secret");
        }
        strcpy(ids[count],v[0]);
        memcpy(keys[count],decoded,sizeof(decoded));
        count++;
        if(!strcmp(v[0],wanted)){
            memcpy(key,decoded,sizeof(decoded));
            seen++;
        }
        p=nl+1;
    }
    OPENSSL_cleanse(decoded,sizeof(decoded));
    OPENSSL_cleanse(keys,sizeof(keys));
    OPENSSL_cleanse(data,n);free(data);
    if(seen!=1)die("unknown controller key");
}
/* PAY-0718: synthetic server ACK identity is separate from controller MAC.
 * One active key per controller. Revoked IDs stay explicit; duplicate key
 * identifiers/material, zero keys and command-key reuse all fail closed.
 * This HMAC test registry is NOT production server key provisioning. */
static void get_server_ack_key(const char *controller,
    const unsigned char commandkey[32],char kid[33],
    unsigned char ackkey[32]) {
    size_t n;char *data=readfile("server-ack-keys.tsv",16384,&n);
    char *p=data,*e=data+n,*v[5];
    char ids[MAX_CTL][33];
    unsigned char keys[MAX_CTL][32],decoded[32];
    int total=0,active=0,i,j,nonzero;
    while(p<e) {
        char *nl=memchr(p,'\n',(size_t)(e-p));
        if(!nl)die("incomplete server ACK registry row");
        *nl=0;
        if(parts(p,v,5)!=4 || !valid_id(v[0]) ||
           !valid_id(v[1]) || !hex64(v[3]) ||
           (strcmp(v[2],"active") && strcmp(v[2],"revoked")) ||
           total>=MAX_CTL)die("invalid server ACK registry");
        unhex(v[3],decoded,32);
        nonzero=0;
        for(j=0;j<32;j++)if(decoded[j])nonzero=1;
        if(!nonzero || CRYPTO_memcmp(decoded,commandkey,32)==0)
            die("server ACK secret weak or reuses command key");
        for(i=0;i<total;i++)
            if(!strcmp(ids[i],v[0]) ||
               CRYPTO_memcmp(keys[i],decoded,32)==0)
                die("duplicate server ACK identity or secret");
        strcpy(ids[total],v[0]);
        memcpy(keys[total],decoded,32);
        total++;
        if(!strcmp(v[1],controller) && !strcmp(v[2],"active")) {
            strcpy(kid,v[0]);
            memcpy(ackkey,decoded,32);
            active++;
        }
        p=nl+1;
    }
    OPENSSL_cleanse(decoded,sizeof(decoded));
    OPENSSL_cleanse(keys,sizeof(keys));
    OPENSSL_cleanse(data,n);free(data);
    if(active!=1)die("server ACK active key absent or ambiguous");
}
static void fault(const char *checkpoint) {
    const char *s=getenv("BLAZE_V2_NATIVE_TEST_FAULT");
    if(s && strcmp(s,checkpoint)==0){
        fprintf(stderr,"V2NATIVE-0668 %s fault%s (no ACK)\n",
                checkpoint,renamed?" UNCERTAIN":"");
        exit(73);
    }
}
static void write_all(int fd,const char *buf,size_t size) {
    size_t pos=0;
    while(pos<size) {
        ssize_t z=write(fd,buf+pos,size-pos);
        if(z<0&&errno==EINTR)continue;
        if(z<=0)die("native staged write failed");
        pos+=(size_t)z;
    }
}
/* PAY-0717 OFF-DEVICE ONLY: signed committed-result receipt. Never emit
 * this receipt until replay is corroborated by the authoritative journal or
 * fsync of the renamed parent directory has succeeded. Domain separation
 * prevents a signed request being mistaken for a server ACK. */
static void emit_receipt(const char *outcome,const char *id,
    unsigned long long seq,const char *fingerprint,
    unsigned long long result,const unsigned char key[32],int signed_ack,
    const char *ack_kid,const unsigned char serverkey[32]) {
    char message[400],signature[65];
    unsigned char mac[EVP_MAX_MD_SIZE];unsigned int count=0;int size;
    if(!signed_ack){printf("%s\t%llu\n",outcome,result);return;}
    if(signed_ack==2) {
        size=snprintf(message,sizeof(message),
          "BLAZE-V2-SERVER-ACK-FIXTURE/1\t%s\t%s\t%llu\t%s\t%llu\t%s\n",
          ack_kid,id,seq,fingerprint,result,outcome);
        if(size<0 || (size_t)size>=sizeof(message))
            die("server ACK canonical payload overflow");
        if(!HMAC(EVP_sha256(),serverkey,32,(unsigned char*)message,
                 (size_t)size,mac,&count) || count!=32)
            die("independent server ACK MAC generation failed");
        hexout(mac,32,signature);
        OPENSSL_cleanse(mac,sizeof(mac));
        printf("ACKV2\t%s\t%s\t%llu\t%s\t%llu\t%s\t%s\n",
            outcome,id,seq,fingerprint,result,ack_kid,signature);
        OPENSSL_cleanse(message,sizeof(message));
        return;
    }
    size=snprintf(message,sizeof(message),
      "BLAZE-V2-ACK-FIXTURE/1\t%s\t%llu\t%s\t%llu\t%s\n",
      id,seq,fingerprint,result,outcome);
    if(size<0 || (size_t)size>=sizeof(message))die("ACK canonical payload overflow");
    if(!HMAC(EVP_sha256(),key,32,(unsigned char*)message,(size_t)size,
         mac,&count) || count!=32)die("ACK MAC generation failed");
    hexout(mac,32,signature);
    OPENSSL_cleanse(mac,sizeof(mac));
    printf("ACKV1\t%s\t%s\t%llu\t%s\t%llu\t%s\n",
      outcome,id,seq,fingerprint,result,signature);
    OPENSSL_cleanse(message,sizeof(message));
}
static void commit(void) {
    char *data=NULL,*all=NULL,checksum[65];
    size_t len=0,total;unsigned char hash[32];
    FILE *ms=open_memstream(&data,&len);int fd,i;
    if(!ms)die("memory stage failed");
    fprintf(ms,"V\t2\n");
    for(i=0;i<nb;i++)fprintf(ms,"A\t%s\t%llu\n",bank[i].name,bank[i].value);
    for(i=0;i<nl;i++)fprintf(ms,"L\t%s\t%llu\n",lease[i].name,lease[i].value);
    for(i=0;i<nc;i++)fprintf(ms,"C\t%s\t%llu\n",ctl[i].name,ctl[i].value);
    for(i=0;i<nr;i++)if(receipts[i].seq>0)
        fprintf(ms,"R\t%s\t%llu\t%s\t%s\t%s\n",receipts[i].ctl,
          receipts[i].seq,receipts[i].event,receipts[i].digest,receipts[i].result);
    if(fclose(ms)!=0)die("output format failed");
    SHA256((unsigned char*)data,len,hash);hexout(hash,32,checksum);
    total=len+2+64+1;
    if(total>MAX_LEDGER)die("snapshot size limit");
    all=malloc(total+1);if(!all)die("output allocation failed");
    memcpy(all,data,len);snprintf(all+len,total-len+1,"H\t%s\n",checksum);
    free(data);
    snprintf(next_name,sizeof(next_name),".v2-next-%ld",(long)getpid());
    fd=openat(dirfd,next_name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0 || !private_fd(fd,0600))die("private stage create refused");
    write_all(fd,all,total);
    OPENSSL_cleanse(all,total);free(all);
    fault("before-source-fsync");
    if(fsync(fd)!=0)die("source fsync failed");
    if(close(fd)!=0)die("source close failed");
    fault("before-rename");
    if(renameat(dirfd,next_name,dirfd,"ledger.tsv")!=0)die("atomic rename failed");
    renamed=1;
    fault("after-rename-before-dir-fsync");
    if(fsync(dirfd)!=0)die("UNCERTAIN parent directory fsync failed");
    fault("after-dir-fsync-before-ack");

}
int main(int argc,char **argv) {
    const char *root,*id,*event,*op,*src,*dst,*hmac;
    unsigned long long seq,units,now,answer=0,high=0,base=0;
    unsigned char key[32],ack_key[32]={0},mac[EVP_MAX_MD_SIZE],sig[32],dig[32];
    char ack_kid[33]={0};
    unsigned int maclen=0;char signed_msg[400],digest_input[400],fingerprint[65];
    size_t n;char *data;struct stat st;
    struct item *floor,*x,*to;
    int i,valid_opcode=0,authenticated_ack=0;
    if(argc!=11 && argc!=12)die("usage: ROOT CTRL SEQ EVENT OP SUBJECT TARGET UNITS NOW HMAC [--authenticated-ack|--server-ack-v2]");
    if(argc==12){
        if(!strcmp(argv[11],"--authenticated-ack"))authenticated_ack=1;
        else if(!strcmp(argv[11],"--server-ack-v2"))authenticated_ack=2;
        else die("unknown response mode");
    }
    root=argv[1];id=argv[2];event=argv[4];op=argv[5];
    src=argv[6];dst=argv[7];hmac=argv[10];
    if(strncmp(root,ROOT_PREFIX,strlen(ROOT_PREFIX)) ||
       !root[strlen(ROOT_PREFIX)] ||
       strchr(root+strlen(ROOT_PREFIX),'/') ||
       strstr(root+strlen(ROOT_PREFIX),".."))
       die("not a strict synthetic fixture root");
    if(!valid_id(id)||!valid_id(src)||
       !(valid_id(dst)||!strcmp(dst,"-"))||
       !hex64(hmac)||!parse_uint(argv[3],100000000ULL,&seq)||seq==0 ||
       !parse_uint(argv[8],31536000ULL,&units)||units==0 ||
       !parse_uint(argv[9],2000000000ULL,&now))
       die("malformed controller envelope");
    valid_opcode=(!strcmp(op,"AM")||!strcmp(op,"SM")||
                  !strcmp(op,"TM")||!strcmp(op,"LR"));
    {char expected[64];
     snprintf(expected,sizeof(expected),"%s:%llu",id,seq);
     if(!valid_opcode || strcmp(event,expected) ||
        (!strcmp(op,"TM") && (!strcmp(dst,"-")||!strcmp(src,dst))) ||
        (strcmp(op,"TM") && strcmp(dst,"-")))
        die("signed event/operation mismatched");
    }
    dirfd=open(root,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(dirfd<0 || fstat(dirfd,&st)!=0 || !S_ISDIR(st.st_mode) ||
       st.st_uid!=geteuid() || (st.st_mode&0777)!=0700)
        die("private fixture directory validation failed");
    data=readfile(".blaze-v2-fixture-only",80,&n);
    if(n!=strlen("BLAZE-V2-SYNTHETIC-ONLY\n") ||
       memcmp(data,"BLAZE-V2-SYNTHETIC-ONLY\n",n))
       die("synthetic marker required");
    free(data);
    lockfd=openat(dirfd,".v2-native-lock",
                  O_CREAT|O_RDWR|O_NOFOLLOW|O_CLOEXEC,0600);
    if(lockfd<0 || !private_fd(lockfd,0600) ||
       flock(lockfd,LOCK_EX|LOCK_NB)!=0)
       die("unsafe/busy v2 native writer lock");
    getkey(id,key);
    unhex(hmac,sig,32);
    if(snprintf(signed_msg,sizeof(signed_msg),
      "BLAZE-V2-AUTH-FIXTURE/1\t%s\t%llu\t%s\t%s\t%s\t%s\t%llu\t%llu\n",
      id,seq,event,op,src,dst,units,now)<0)
       die("envelope format failed");
    if(!HMAC(EVP_sha256(),key,32,(unsigned char*)signed_msg,
         strlen(signed_msg),mac,&maclen) || maclen!=32 ||
         CRYPTO_memcmp(sig,mac,32)!=0)
       die("signed controller envelope mismatch");
    /* Refuse a financial commit unless the independently configured server
       ACK signing identity is validated BEFORE any journal mutation. */
    if(authenticated_ack==2)
        get_server_ack_key(id,key,ack_kid,ack_key);
    if(snprintf(digest_input,sizeof(digest_input),
         "%s|%llu|%s|%s|%s|%s|%llu|%llu|v2",
         id,seq,event,op,src,dst,units,now)<0)
       die("fingerprint format failed");
    SHA256((unsigned char*)digest_input,strlen(digest_input),dig);
    hexout(dig,32,fingerprint);
    data=readfile("ledger.tsv",MAX_LEDGER,&n);
    parseledger(data,n);free(data);
    validate_receipts();
    floor=find(ctl,nc,id);
    high=floor?floor->value:0;
    for(i=0;i<nr;i++)if(!strcmp(receipts[i].ctl,id) &&
                       receipts[i].seq==seq){
        if(strcmp(receipts[i].event,event) ||
           CRYPTO_memcmp(receipts[i].digest,fingerprint,64)!=0)
            die("controller sequence payload collision");
        {unsigned long long saved=0;
         if(!parse_uint(receipts[i].result,2000000000ULL,&saved))
             die("replay receipt amount malformed");
         /* PAY-0745: a rename visible after an interrupted dir-fsync is not
          * a durable commit. Confirm parent directory under exclusive lock
          * before sending a retained-sequence replay ACK. Fixture only. */
         fault("before-replay-dir-fsync");
         if(fsync(dirfd)!=0)die("UNCERTAIN replay parent directory fsync failed");
         emit_receipt("REPLAY",id,seq,fingerprint,saved,key,authenticated_ack,
                      ack_kid,ack_key);
         OPENSSL_cleanse(key,sizeof(key));
         OPENSSL_cleanse(ack_key,sizeof(ack_key));
        }
        return 0;
    }
    if(seq<=high)die("stale controller sequence");
    if(seq!=high+1)die("out-of-order controller sequence");
    if(!floor && nc==MAX_CTL)die("controller ceiling");
    if(!strcmp(op,"LR")){
        x=find(lease,nl,src);
        if(!x)die("unknown rental lease");
        base=(x->value>now?x->value:now);
        if(base>2000000000ULL-units)die("rental lease overflow");
        x->value=base+units;answer=x->value;
    }else{
        x=find(bank,nb,src);
        if(!x)die("unknown member bank");
        if(!strcmp(op,"AM")){
            if(x->value>2000000000ULL-units)die("member credit overflow");
            x->value+=units;
        }else if(!strcmp(op,"SM")){
            if(x->value<units)die("insufficient time");
            x->value-=units;
        }else{
            to=find(bank,nb,dst);
            if(!to||x->value<units||
               to->value>2000000000ULL-units)
               die("invalid prepaid transfer");
            x->value-=units;to->value+=units;
        }
        answer=x->value;
    }
    if(!floor){floor=&ctl[nc++];strcpy(floor->name,id);}
    floor->value=seq;
    for(i=0;i<nr;){
        if(!strcmp(receipts[i].ctl,id) &&
           seq>=8 && receipts[i].seq<=seq-8)
            receipts[i]=receipts[--nr];
        else i++;
    }
    if(nr>=MAX_RECEIPT)die("receipt quota exhausted");
    {struct receipt *entry=&receipts[nr++];
     strcpy(entry->ctl,id);entry->seq=seq;strcpy(entry->event,event);
     strcpy(entry->digest,fingerprint);
     snprintf(entry->result,sizeof(entry->result),"%llu",answer);
    }
    commit();
    emit_receipt("COMMIT",id,seq,fingerprint,answer,key,authenticated_ack,
                 ack_kid,ack_key);
    OPENSSL_cleanse(key,sizeof(key));
         OPENSSL_cleanse(ack_key,sizeof(ack_key));
    return 0;
}
