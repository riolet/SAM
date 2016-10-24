function get_mock_m_ports() {
    response = {
    "443": {
      "port": 443,
      "active": 1,
      "name": "https",
      "description": "http protocol over TLS/SSL",
      "alias_name": null,
      "alias_description": null
    },
    "3268": {
      "port": 3268,
      "active": 1,
      "name": "msft-gc",
      "description": "Microsoft Global Catalog",
      "alias_name": "other name",
      "alias_description": "other description"
    },
    "7680": {
      "port": 7680,
      "active": 1,
      "name": "pando-pub",
      "description": "Pando Media Public Distribution",
      "alias_name": '',
      "alias_description": null
    },
    "8081": {
      "port": 8081,
      "active": 0,
      "name": "sunproxyad",
      "description": "Sun Proxy Admin Service",
      "alias_name": null,
      "alias_description": null
    }
    };

    //clear any existing data
    ports.ports = [];

    ports.private.GET_response(response);

//    Object.keys(response).forEach(function (key) {
//        ports.set(Number(key), response[key]);
//    });
}