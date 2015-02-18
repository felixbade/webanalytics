from ipaddress import ip_address, ip_network

from ipwhois import IPWhois

known_networks = {}

def updateIpInfo(ip):
    info = IPWhois(ip).lookup()
    # these two lines might break on some input
    net = info['nets'][0]
    networks = net['cidr'].split(', ')
    for network in networks:
        network = ip_network(network)
        known_networks.update({network: net})
    return net

def getIpInfo(ip):
    ip = ip_address(ip)
    for network in known_networks:
        if ip in network:
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
