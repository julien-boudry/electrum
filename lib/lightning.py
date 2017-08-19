import sys
sys.path.insert(0, "lib/ln")
from .ln import rpc_pb2_grpc, rpc_pb2
import os
from . import keystore, bitcoin

import grpc
import concurrent.futures as futures
import time

rand = os.urandom(32)
#k = keystore.BIP32_KeyStore({})
#k.add_xprv_from_seed(rand, 0, 'm/0/0')
#assert k.xpub is not None
#pubkey = bytearray.fromhex(k.derive_pubkey(False, 0))
#print(pubkey)
K, K_compressed = bitcoin.get_pubkeys_from_secret(rand)
pubk = bitcoin.public_key_to_p2wpkh(K_compressed) # really compressed?
print(pubk)

# this should fail because we are on simnet
adr = keystore.xpubkey_to_address('fd007d260305ef27224bbcf6cf5238d2b3638b5a78d5')[1]
print(adr)
assert adr != '1CQj15y1N7LDHp7wTt28eoD1QhHgFgxECH'

class LightningImpl(rpc_pb2_grpc.ElectrumBridgeServicer):
  def NewAddress(self, request, context):
    m = rpc_pb2.NewAddressResponse()
    m.address = pubk
    return m

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  rpc_pb2_grpc.add_ElectrumBridgeServicer_to_server(
      LightningImpl(), server)
  server.add_insecure_port('[::]:9090')
  server.start()
  try:
    while True:
      time.sleep(10)
  except KeyboardInterrupt:
    server.stop(0)

def test_lightning(wallet):
  serve()

if __name__ == '__main__':
  serve()
