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

parser = ArgumentParser(description="DCTCP")
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
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=200)

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

parser.add_argument('--enable-dctcp',
                    dest="enable_dctcp",
                    type=int,
                    help="Enable DCTCP or not",
                    default=0)

parser.add_argument('--expt',
                    type=int,
                    help="Experiment to run",
                    default=1)

parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="mdtcp")

# Expt parameters
args = parser.parse_args()

class DCTopo(Topo):
    "Simple topology for DCTCP experiment."

    def __init__(self, n=4):
        super(DCTopo, self).__init__()
        #ECN in Linux is implemented using RED. The below set RED parameters 
        #to maintain K=20 packets where a packet size if 1500 bytes and we mark
        #packets with a probability of 1.
        self.red_params = {'min':30000, #K=20pkts
                           'max':30001,
                           'avpkt':1500,
                           'burst':20,
			   'prob':1,
                           'limit':1000000,
                           }
                           
        # Adding senders
        # hosts=[]
        h0=self.addHost('h0',ip='10.0.1.1')
        h1=self.addHost('h1',ip='10.0.2.1')
        h2=self.addHost('h2',ip='10.0.3.1')
        h3=self.addHost('h3',ip='10.0.4.1')
        # for i in range(n):
        #   # hosts.append(self.addHost('h%d' % i,ip='10.0.'+str(i+1)+'.1'))
        #   hosts+'_'+str(i)=self.addHost('h%d' % i,ip='10.0.'+str(i+1)+'.1')
          # h1 = net.addHost( 'h1', ip='10.0.1.1')



        # Adding switch
        sw0=self.addSwitch('s0')
        sw1=self.addSwitch('s1')
        # switches=[]
        # switches.append(self.addSwitch('s0'))
        # switches.append(self.addSwitch('s1'))

        # Configuration of sender, receiver and switch
        senderConfig   = {'bw':args.bw_sender, 
                          'delay':args.delay,
                          'max_queue_size':args.maxq}

        receiverConfig = {'bw':args.bw_receiver, 
                          'delay':args.delay,
                          'max_queue_size':args.maxq}

        switchConfig   = {'enable_ecn': args.enable_ecn, 
			  'enable_red': args.enable_ecn, 
                          'red_params': self.red_params \
                                        if args.enable_ecn is 1 else None,
                          'bw':args.bw_receiver,
			  'delay':0,
			  'max_queue_size':args.maxq}

        bottleneckConfig = {'params1': receiverConfig,
                            'params2': switchConfig}
        # Adding link between switches
        self.addLink(sw1,sw0,cls=Link,cls1=TCIntf,cls2=TCIntf,params1=receiverConfig, params2=switchConfig)

        
        # Adding link from the switch to the rcvr.
        self.addLink(h2, sw1, **receiverConfig)
        self.addLink(h2, sw1, **receiverConfig)
        self.addLink(h3, sw1, **receiverConfig)

        # Adding link from the switch to the rcvr.
        self.addLink(h0, sw0, **senderConfig)
        self.addLink(h0, sw0, **senderConfig)
        self.addLink(h1, sw0, **senderConfig)



       

        
        # # Adding link from the switch to the rcvr.
        # self.addLink('h3', switch[1], cls=Link, cls1=TCIntf, cls2=TCIntf, 
        #               params1=receiverConfig, params2=switchConfig)


        # # Adding links from the switch to the senders (hosts)
        # for i in range(1,n):
        #   self.addLink('h%s' % i, switch, **senderConfig)

        return

def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > %s/%s" % (args.dir, outfile),
          shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
    h2 = net.get('h2')
    h3 = net.get('h3')

    h0=net.get('h0')
    h1=net.get('h1')
    Popen("killall -s 9 tshark",shell=True).wait()
    Popen("killall -s 9 iperf",shell=True).wait()


    print 'starting capturing...',
    print h0.cmd('tshark -f "tcp" -i any -a duration:'+str(120+1)+' -T pdml '+
          ' | sed -e "s/30313233343536373839//g" '+     # remove unimportant test data, generated by iperf
          ' | sed -e "s/30:31:32:33:34:35:36:37:38:39://g" '+
          ' >mdtcp_cap.txt &'),
    print h1.cmd('tshark -f "tcp" -i any -a duration:'+str(120+1)+' -T pdml '+
          ' | sed -e "s/30313233343536373839//g" '+     # remove unimportant test data, generated by iperf
          ' | sed -e "s/30:31:32:33:34:35:36:37:38:39://g" '+
          ' >dctcp_cap.txt &'),
    sleep(1) # wait for tshark to startup
    print '...capture started\n'

    

    print "Starting iperf server..."
    mp_server = h2.popen("iperf -s -t 125 -w 16m")
    dc_server = h3.popen("iperf -s -t 125 -w 16m")
    
    mp_clnt=h0.popen("iperf -c %s -p 5001 -t 120 -i 1 > iperf_bandwith_mdtcp_log.txt & " %(h2.IP()), shell=True)

    dc_clnt=h1.popen("iperf -c %s -p 5001 -t 120 -i 1 > iperf_bandwith_dctcp_log.txt & " %(h3.IP()), shell=True)




    # for i in range(1,args.n):
    #   h = net.get('h%s' % i)
    #   print "Starting iperf receiver h%d"%i
    #   # long lived TCP flow from clients to server at h0.
    #   client = h.popen("iperf -c %s -p 5001 -t 3600" %(h0.IP()), 
    #                   shell=True)
    return

def start_delayed_iperf(net):
    h0 = net.get('h0')
    print "delayed Starting iperf server..."
    h0.cmd("iperf -s -w 16m -i 1 > %s/iperfRecv.txt &"%args.dir)

    t = 270
    for i in range(1,args.n):
      h = net.get('h%s' % i)
      print "Starting iperf sender h%d"%i
      # long lived TCP flow from client to server h0.
      h.cmd("iperf -c %s -p 5001 -t %d -i 1 > %s/iperf%d.txt &"\
            %(h0.IP(),t,args.dir,i))
      t = t - 60
      #to simulate each flow starting after 30s from previous flow
      sleep(30)

def comparison(net):
    start_iperf(net)
    sleep(30)

def dctcp():    
    if not os.path.exists(args.dir): 
      os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = DCTopo(n=args.n)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)

    h2 = net.get('h2')
    h2.setIP('10.0.3.1', intf='h2-eth0')
    h2.setIP('10.0.3.2', intf='h2-eth1')
    h3 = net.get('h3')

    h0=net.get('h0')
    h0.setIP('10.0.1.1', intf='h0-eth0')
    h0.setIP('10.0.1.2', intf='h0-eth1')
    h1=net.get('h1')


    net.start()
    sleep(1) # wait for net to startup (unless this, it might won't work...)
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    # net.pingAll()

    if args.expt is 1:
      comparison(net)

    if args.expt is 2:
       convergence(net)

    # Start all the monitoring processes
    start_tcpprobe("cwnd.txt")

    # Start monitoring the queue sizes. 
    qmon = start_qmon(iface='s0-eth1',
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
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    #Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

def enableDCTCP():
    os.system("sudo sysctl -w net.mptcp.mptcp_enabled=1")
    os.system("sudo sysctl -w net.mptcp.mptcp_path_manager=fullmesh")
    os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=mdtcp")


def disableDCTCP():
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
      enableDCTCP()
      enableECN()
    
    dctcp()
