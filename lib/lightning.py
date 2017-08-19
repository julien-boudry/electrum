import sys
sys.path.insert(0, "lib/ln")
from .ln import rpc_pb2_grpc, rpc_pb2
import os
from . import keystore, bitcoin

import grpc
import concurrent.futures as futures
import time

WALLET = None

rand = os.urandom(32)
#k = keystore.BIP32_KeyStore({})
#k.add_xprv_from_seed(rand, 0, 'm/0/0')
#assert k.xpub is not None
#pubkey = bytearray.fromhex(k.derive_pubkey(False, 0))
#print(pubkey)
K, K_compressed = bitcoin.get_pubkeys_from_secret(rand)
pubk = bitcoin.public_key_to_p2pkh(K_compressed) # really compressed?
print(pubk)
assert len(pubk) <= 35

class LightningImpl(rpc_pb2_grpc.ElectrumBridgeServicer):
  def ConfirmedBalance(self, request, context):
    m = rpc_pb2.ConfirmedBalanceResponse()
    m.amount = 100
    return m
  def NewAddress(self, request, context):
    m = rpc_pb2.NewAddressResponse()
    m.address = pubk
    return m
  def FetchRootKey(self, request, context):
    m = rpc_pb2.FetchRootKeyResponse()
    m.rootKey = bytes([1,2,3])
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
  global WALLET
  WALLET = wallet
  serve()

if __name__ == '__main__':
  serve()
