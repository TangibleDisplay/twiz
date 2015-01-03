from osc import listen, bind, readQueue


def main(host='0.0.0.0', port=8000, address='/update'):
    oscid = listen(host, port)
    bind(oscid, dump_data, address)
    while True:
        readQueue(oscid)


def dump_data(osc_data, *args):
    address = osc_data[0]
    types = osc_data[1]
    data = osc_data[2:]
    print(address, types, data)


if __name__ == '__main__':
    main()
