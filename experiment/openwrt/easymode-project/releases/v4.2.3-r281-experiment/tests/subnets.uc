import {overlaps} from '/usr/share/blaze/subnets.uc';
for(let c in [
 ['10.0.121.253',24,'192.168.1.1','255.255.255.0',false],
 ['10.0.121.253',24,'192.168.253.1',24,false],
 ['192.168.1.20',24,'192.168.1.1',24,true],
 ['10.0.1.20',16,'10.0.121.1',24,true],
 ['10.0.1.20',24,'10.0.121.1',16,true],
 ['10.0.121.253',24,'192.168.254.1',24,false]
])if(overlaps(c[0],c[1],c[2],c[3])!=c[4])die('Subnet comparison failed');
print('PASS: dotted and prefix masks, disjoint and overlapping networks\n');
