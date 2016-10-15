function get_mock_m_ports() {
  var m_ports = []
  m_ports[443] = {
    "active": 1,
    "port": 443,
    "name": "https",
    "description": "http protocol over TLS/SSL",
    "alias_name": null,
    "alias_description": null
  };
  m_ports[3268] = {
    "active": 1,
    "port": 3268,
    "name": "msft-gc",
    "description": "Microsoft Global Catalog",
    "alias_name": "other name",
    "alias_description": "other description"
  };
  m_ports[7680] = {
    "active": 1,
    "port": 7680,
    "name": "pando-pub",
    "description": "Pando Media Public Distribution",
    "alias_name": "",
    "alias_description": null
  };
  m_ports[8081] = {
    "active": 0,
    "port": 8081,
    "name": "sunproxyad",
    "description": "Sun Proxy Admin Service",
    "alias_name": null,
    "alias_description": null
  };
  return m_ports;
}