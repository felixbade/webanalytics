from ipaddress import ip_address, ip_network
import shelve

from ipwhois import IPWhois

ip_whois_shelve_filename = 'ip_whois'
known_networks = shelve.open(ip_whois_shelve_filename)

def updateIpInfo(ip):
    info = IPWhois(ip).lookup()
    # these two lines might break on some input
    net = info['nets'][0]
    networks = net['cidr'].split(', ')
    for network in networks:
        network = network
        known_networks.update({network: net})
    return net

def getIpInfo(ip):
    ip = ip_address(ip)
    for network in known_networks:
        if ip in ip_network(network):
            info = known_networks[network]
            return info
    info = updateIpInfo(ip)
    return info

def getISP(ip):
    net = getIpInfo(ip)
    return net['description']
    
def getCountry(ip):
    net = getIpInfo(ip)
    return net['country']
