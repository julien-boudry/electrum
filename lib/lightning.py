import sys
sys.path.insert(0, "lib/ln")
from .ln import rpc_pb2_grpc

import grpc
import concurrent.futures as futures
import time

class LightningImpl(rpc_pb2_grpc.ElectrumBridgeServicer):
  pass

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  rpc_pb2_grpc.add_ElectrumBridgeServicer_to_server(
      rpc_pb2_grpc.ElectrumBridgeServicer(), server)
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
