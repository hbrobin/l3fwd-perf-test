package.path = package.path ..";?.lua;test/?.lua;app/?.lua;"

--pktgen.page("range");

-- Port 0 3c:fd:fe:9c:5c:d8,  Port 1 3c:fd:fe:9c:5c:b8
pktgen.range.dst_mac("0", "start", "00:11:22:33:20:11");
pktgen.range.src_mac("0", "start", "24:8a:07:b5:6f:a4");

pktgen.range.dst_ip("0", "start", "2.1.1.1");
pktgen.range.dst_ip("0", "inc", "0.0.0.1");
pktgen.range.dst_ip("0", "min", "2.1.1.1");
pktgen.range.dst_ip("0", "max", "2.1.1.125");

pktgen.range.src_ip("0", "start", "2.1.1.126");
pktgen.range.src_ip("0", "inc", "0.0.0.1");
pktgen.range.src_ip("0", "min", "2.1.1.126");
pktgen.range.src_ip("0", "max", "2.1.1.254");

pktgen.range.ip_proto("0", "udp");

pktgen.range.dst_port("0", "start", 2000);
pktgen.range.dst_port("0", "inc", 1);
pktgen.range.dst_port("0", "min", 2000);
pktgen.range.dst_port("0", "max", 4000);

pktgen.range.src_port("0", "start", 5000);
pktgen.range.src_port("0", "inc", 1);
pktgen.range.src_port("0", "min", 5000);
pktgen.range.src_port("0", "max", 7000);

pktgen.range.pkt_size("0", "start", 512);
pktgen.range.pkt_size("0", "inc", 0);
pktgen.range.pkt_size("0", "min", 512);
pktgen.range.pkt_size("0", "max", 512);

-- Set up second port
pktgen.range.dst_mac("1", "start", "00:22:22:33:20:21");
pktgen.range.src_mac("1", "start", "24:8a:07:b5:6f:80");

pktgen.range.dst_ip("1", "start", "1.1.1.1");
pktgen.range.dst_ip("1", "inc", "0.0.0.1");
pktgen.range.dst_ip("1", "min", "1.1.1.1");
pktgen.range.dst_ip("1", "max", "1.1.1.125");

pktgen.range.src_ip("1", "start", "2.1.1.126");
pktgen.range.src_ip("1", "inc", "0.0.0.1");
pktgen.range.src_ip("1", "min", "2.1.1.1");
pktgen.range.src_ip("1", "max", "2.1.1.126");

pktgen.range.ip_proto("1", "udp");

pktgen.range.dst_port("1", "start", 5000);
pktgen.range.dst_port("1", "inc", 1);
pktgen.range.dst_port("1", "min", 5000);
pktgen.range.dst_port("1", "max", 7000);

pktgen.range.src_port("1", "start", 2000);
pktgen.range.src_port("1", "inc", 1);
pktgen.range.src_port("1", "min", 2000);
pktgen.range.src_port("1", "max", 4000);

pktgen.range.pkt_size("1", "start", 512);
pktgen.range.pkt_size("1", "inc", 0);
pktgen.range.pkt_size("1", "min", 512);
pktgen.range.pkt_size("1", "max", 512);

pktgen.set_range("all", "on");
