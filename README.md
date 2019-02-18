# l3fwd-perf-test
A simple test framework for l3fwd performance test in DUT and using pktgen as traffic generator

# This test framework is use for...
- Save effort to install versions of dpdk/pktgen
- Save effort to collect perf from different core/pkt lens/queues configurations
- Collect “stable” perf result (average)
- Save effort of fill in perf result data manually, auto generate csv file
- Collect bidirectional/unidirectional in one run

# An overview of the test framework
![image](https://github.com/hbrobin/l3fwd-perf-test/raw/master/img/overview.png)
