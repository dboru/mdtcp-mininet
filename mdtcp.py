#!/usr/bin/python
"MDTCP Test"


from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.link import Link
from mininet.link import TCIntf
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen
import termcolor as T
# import time
import sys
import os
import math
from math import sqrt

parser = ArgumentParser(description="MDTCP")
parser.add_argument('--bw-sender', '-B',
                    dest="bw_sender",
                    type=float,
                    help="Bandwidth of sender link (Mb/s)",
                    default=1000)

parser.add_argument('--bw-receiver', '-b',
                    dest="bw_receiver",
                    type=float,
                    help="Bandwidth of receiver link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=30)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=200)

parser.add_argument('--n',
                    type=int,
                    help="Number of hosts",
                    default=4)

parser.add_argument('--enable-ecn',
                    dest="enable_ecn",
                    type=int,
                    help="Enable ECN or not",
                    default=0)
parser.add_argument('--enable-red',
                    dest="enable_red",
                    type=int,
                    help="Enable RED or not",
                    default=0)
parser.add_argument('--redmin',
                    type=int,
                    help="RED min pkts",
                    default=30000)
parser.add_argument('--redmax',
                    type=int,
                    help="RED max pkts",
                    default=30000)
parser.add_argument('--redburst',
                    type=int,
                    help="RED burst pkts",
                    default=20)
parser.add_argument('--redlimit',
                    type=int,
                    help="RED limit pkts",
                    default=100000)
parser.add_argument('--redprob',
                    type=float,
                    help="RED probability",
                    default=1)
parser.add_argument('--redavpkt',
                    type=int,
                    help="RED avpkt",
                    default=1500)

parser.add_argument('--enable-mdtcp',
                    dest="enable_mdtcp",
                    type=int,
                    help="Enable MDTCP or not",
                    default=0)

parser.add_argument('--expt',
                    type=int,
                    help="Experiment to run",
                    default=1)
parser.add_argument('--intf',
                    type=int,
                    help="No. of interfaces",
                    default=2)

parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="mdtcp")

# Expt parameters
args = parser.parse_args()

class NetTopo(Topo):
    "Simple topology for MDTCP experiment."

    def __init__(self, n=4):
        super(NetTopo, self).__init__()
        #ECN in Linux is implemented using RED. The below set RED parameters 
        #to maintain K=20 packets where a packet size if 1500 bytes and we mark
        #packets with a probability of 1.
        self.red_params = {'min':args.redmin, #K=20pkts
                           'max':args.redmax,
                           'avpkt':1500,
                           'burst':args.redburst,
                           'prob':args.redprob,
                           'limit':args.redlimit,
                           }
                           
        
        h2=self.addHost('h2',ip='10.0.1.2')
        h3=self.addHost('h3',ip='10.0.2.2')

        h0=self.addHost('h0',ip='10.0.4.2')
        h1=self.addHost('h1',ip='10.0.3.3')
     

        # Adding switch
        sw0=self.addSwitch('s0')
        sw1=self.addSwitch('s1')
        # Configuration of sender, receiver and switch
        senderConfig   = {'bw':args.bw_sender, 
                          'delay':args.delay,
                          'max_queue_size':args.maxq}

        receiverConfig = {'bw':args.bw_receiver, 
                          'delay':args.delay,
                          'max_queue_size':args.maxq}
       
        switchConfig   = { 'bw': args.bw_receiver,
                           'delay':args.delay,
                           'max_queue_size':args.maxq,
                           'enable_ecn': True if args.enable_ecn else False,
                           'enable_red': True if args.enable_red else False,
                           'red_min': args.redmin,
                           'red_max': args.redmax,
                           'red_burst':  args.redburst,
                           'red_prob':args.redprob,
                           'red_avpkt': args.redavpkt,
                           'red_limit': args.redlimit                    
                           }
    

        self.addLink(sw1,sw0,cls=Link,cls1=TCIntf,cls2=TCIntf,params1=switchConfig, params2=switchConfig)

        for i in range(args.intf):
            self.addLink(h0, sw0, **senderConfig)
        self.addLink(h1, sw1, **receiverConfig)
        self.addLink(h2, sw0, **senderConfig)
        self.addLink(h3, sw1, **receiverConfig)
        
        return

def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > %s/%s" % (args.dir, outfile),
          shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()

def start_qmon(iface, interval_sec=0.001, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
    h2 = net.get('h2')
    h3 = net.get('h3')
    h0=net.get('h0')
    h1=net.get('h1')
    # Popen("killall -s 9 tshark",shell=True).wait()
    Popen("killall -s 9 iperf",shell=True).wait()
    Popen("killall -s 9 tcpdump",shell=True).wait()
    Popen("tcpdump -i s1-eth1 -s 96 -w mdtcp-dump", shell=True)
    sleep(1) # wait for tshark to startup
    print '...capture started\n'
  
    print "Starting iperf server..."
    mp_server = h0.popen("iperf -s -i 1 -w 16m")
    dc_server = h2.popen("iperf -s -i 1 -w 16m")
    # dcsrv=h4.popen("iperf -s -w 16m")
    mp_clnt=h1.popen("iperf -c %s -p 5001 -t %d -i 1 > iperf_bandwith_mdtcp_log.txt & " %(h0.IP(),args.time), shell=True)
    dc_clnt=h3.popen("iperf -c %s -p 5001 -t %d -i 1 > iperf_bandwith_dctcp_log.txt & " %(h2.IP(),args.time), shell=True)
    return

def set_red(iface, red_params,args_bw_net):
    "Change RED params for interface"
    cmd=("tc qdisc del dev %s root" %(iface))
    os.system(cmd)
    cmd = ("tc qdisc add dev %s root handle 4: "
           "red limit %s min %s max %s avpkt %s "
       "burst %s bandwidth %sMbit probability %s ecn" % (iface, args.redlimit, args.redmin, \
        args.redmax, args.redavpkt, args.redburst, args_bw_net, args.redprob))
    os.system(cmd)

def comparison(net):
    start_iperf(net)
    sleep(2)

def mdtcp():    
    if not os.path.exists(args.dir): 
      os.makedirs(args.dir)
    # os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo =NetTopo(n=args.n)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)

    h0 = net.get('h0')
    h1 = net.get('h1')

    for i in range(args.intf):
        ip='10.0.%s.2'%str(i+4)
        etf='h0-eth%s'%str(i)
        h0.setIP(ip, intf=etf)
       
        lg.info("configuring source-specific routing tables for MPTCP\n")
        h0.cmdPrint("ip rule add from 10.1.%s.2 table 1",i+4)
        h0.cmdPrint("ip route add 10.1.%s.0/24 dev h0-eth0 scope link table %s",(i+4,i+1))
        h0.cmdPrint("ip route add default via 10.1.1.1 dev h0-eth%s table %s",(i,i+1))

    net.start()
    sleep(1) # wait for net to startup (unless this, it might won't work...)
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()


    if args.expt is 1:
      comparison(net)

    if args.expt is 2:
       convergence(net)

    # Start all the monitoring processes
    start_tcpprobe("cwnd.txt")

    # Start monitoring the queue sizes. 
    qmon = start_qmon(iface='s1-eth1',
                      outfile='%s/q.txt' % (args.dir))

    start_time = time()
    while True:
        now = time()
        delta = now - start_time
        if delta > args.time:
            break

    stop_tcpprobe()
    qmon.terminate()
    net.stop()
    Popen("killall -s 9 iperf",shell=True).wait()
  
def enableMDTCP():
    os.system("sudo sysctl -w net.mptcp.mptcp_enabled=1")
    os.system("sudo sysctl -w net.mptcp.mptcp_path_manager=fullmesh")
    os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=mdtcp")
    # os.system("sudo echo -n 4 > /sys/module/mptcp_ndiffports/parameters/num_subflows")
def enableMPTCP():
    os.system("sudo sysctl -w net.mptcp.mptcp_enabled=1")
    os.system("sudo sysctl -w net.mptcp.mptcp_path_manager=fullmesh")
    os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=olia")
    # os.system("sudo sysctl -w net.ipv4.tcp_dctcp_enable=1")
    # os.system("sudo sysctl -w net.ipv4.tcp_dctcp_clamp_alpha_on_loss=0")
    # os.system("sudo echo -n 2 > /sys/module/mptcp_ndiffports/parameters/num_subflows")

def disableMDTCP():
    os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=reno")
def enableECN():
    os.system("sudo sysctl -w net.ipv4.tcp_ecn=1")
def disableECN():
    os.system("sudo sysctl -w net.ipv4.tcp_ecn=0")

def convergence(net):
    start_delayed_iperf(net)
if __name__ == "__main__":
    # disableDCTCP()
    # disableECN()
    if (args.enable_ecn):
        enableECN()
        enableMDTCP()
    elif (args.enable_red and not args.enable_ecn):
        enableMPTCP()
        disableECN()
     
    mdtcp()

# tcp_probe format 
# time srcip:port destip:port pkt_length snd_nxt_seqno snd_una_seq cwnd ssthresh snd_wnd srtt(us) rcv_wnd

# return scnprintf(tbuf, n,
#             "%lu.%09lu %pISpc %pISpc %d %#x %#x %u %u %u %u %u\n",
#             (unsigned long)ts.tv_sec,
#             (unsigned long)ts.tv_nsec,
#             &p->src, &p->dst, p->length, p->snd_nxt, p->snd_una,
#             p->snd_cwnd, p->ssthresh, p->snd_wnd, p->srtt, p->rcv_wnd);
