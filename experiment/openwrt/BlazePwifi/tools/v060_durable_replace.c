/*
 * FSYNC-0643 — OFF-DEVICE synthetic durability syscall fixture ONLY.
 * It is NOT an authenticated payment ledger and is NOT installed in rootfs.
 * Usage: v060_durable_replace /tmp/blaze-v2-atomic-XXXXXX src-name dst-name
 * Strictly prevents writes to customer devices or arbitrary paths.
 *
 * Success protocol: source fsync -> same-directory atomic renameat ->
 *                   parent directory fsync -> COMMITTED ACK.
 * Before-rename failure: destination unchanged; after-rename failure:
 * destination uncertain; caller MUST reconcile, never blindly retry money.
 * Compile with -DBLAZE_FIXTURE_ONLY for injected laboratory crashes.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define PREFIX "/tmp/blaze-v2-atomic-"
#define MARKER ".blaze-v2-fixture-only"
#define MAGIC "BLAZE-V2-SYNTHETIC-ONLY\n"

static int valid_name(const char *p) {
    size_t n;
    if (!p || !(('A'<=p[0]&&p[0]<='Z') ||
                ('a'<=p[0]&&p[0]<='z') ||
                ('0'<=p[0]&&p[0]<='9'))) return 0;
    for (n=1; p[n]; ++n) {
        char c=p[n];
        if (!(('A'<=c&&c<='Z') || ('a'<=c&&c<='z') ||
              ('0'<=c&&c<='9') || c=='_' || c=='-' || c=='.'))
            return 0;
    }
    return n<96;
}

static int private_regular(int fd) {
    struct stat s;
    return (fstat(fd,&s)==0 && S_ISREG(s.st_mode) &&
            s.st_nlink==1 && !(s.st_mode&0022));
}

static int valid_marker(int rootfd) {
    int fd=openat(rootfd,MARKER,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    char text[sizeof(MAGIC)+8];
    ssize_t n;
    if (fd<0) return 0;
    if (!private_regular(fd)) {close(fd);return 0;}
    n=read(fd,text,sizeof(text));
    if (close(fd)!=0 || n!=(ssize_t)strlen(MAGIC))return 0;
    return memcmp(text,MAGIC,(size_t)n)==0;
}

static int fail(const char *where, int code) {
    fprintf(stderr,"FSYNC-0643 %s: %s (no success ACK)\n",
            where,strerror(errno));
    return code;
}

#ifdef BLAZE_FIXTURE_ONLY
static int injected(const char *point) {
    const char *v=getenv("BLAZE_DURABLE_TEST_FAULT");
    return v && strcmp(v,point)==0;
}
#else
static int injected(const char *point) {(void)point;return 0;}
#endif

int main(int argc,char **argv) {
    int dirfd=-1,srcfd=-1,existing=-1,rc=3;
    struct stat st;
    const char *root,*src,*dst;
    if (argc!=4) {fputs("usage: synthetic ROOT SRC_BASENAME DST_BASENAME\n",stderr);return 2;}
    root=argv[1];src=argv[2];dst=argv[3];
    if (strncmp(root,PREFIX,strlen(PREFIX))!=0 ||
        root[strlen(PREFIX)]=='\0' || strchr(root+strlen(PREFIX),'/') ||
        !valid_name(src) || !valid_name(dst) || strcmp(src,dst)==0) {
        fputs("FSYNC-0643 refused nonfixture path or basename\n",stderr);
        return 2;
    }
    dirfd=open(root,O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
    if (dirfd<0) return fail("opening test directory",3);
    if (fstat(dirfd,&st)!=0 || !S_ISDIR(st.st_mode) ||
        (st.st_mode&0022) || st.st_nlink<2 || !valid_marker(dirfd)) {
        errno=EPERM;rc=fail("fixture marker/directory validation",3);goto done;
    }
    srcfd=openat(dirfd,src,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
    if (srcfd<0 || !private_regular(srcfd)) {
        errno=EPERM;rc=fail("private source validation",3);goto done;
    }
    /* Reject destinations that are symbolic links, directories or multi-
       linked originals. A missing destination is permitted for bootstrap. */
    existing=openat(dirfd,dst,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
    if (existing>=0) {
        if (!private_regular(existing)) {
            errno=EPERM;rc=fail("private destination validation",3);goto done;
        }
    } else if (errno!=ENOENT) {
        rc=fail("destination stat refused",3);goto done;
    }
    if (injected("before-source-fsync")) {
        errno=EIO;rc=fail("injected before-source-fsync",70);goto done;
    }
    if (fsync(srcfd)!=0) {rc=fail("source fsync",70);goto done;}
    if (injected("before-rename")) {
        errno=EIO;rc=fail("injected before-rename",71);goto done;
    }
    if (renameat(dirfd,src,dirfd,dst)!=0) {
        rc=fail("same-directory renameat",71);goto done;
    }
    /* The destination may now have changed even if the next fsync fails.
       NEVER emit an ACK on this failure or roll back from an old image. */
    if (injected("after-rename-before-dir-fsync")) {
        errno=EIO;rc=fail("UNCERTAIN injected after rename",73);goto done;
    }
    if (fsync(dirfd)!=0) {rc=fail("UNCERTAIN parent fsync",73);goto done;}
    puts("COMMITTED");
    rc=0;
done:
    if (existing>=0)close(existing);
    if (srcfd>=0)close(srcfd);
    if (dirfd>=0)close(dirfd);
    return rc;
}
