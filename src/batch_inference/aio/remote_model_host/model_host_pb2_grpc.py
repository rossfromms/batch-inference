# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from batch_inference.aio.remote_model_host import \
    model_host_pb2 as \
    batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2


class ModelHostStub:
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.predict = channel.unary_unary(
            "/ModelHost/predict",
            request_serializer=batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Request.SerializeToString,
            response_deserializer=batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Response.FromString,
        )


class ModelHostServicer:
    """Missing associated documentation comment in .proto file."""

    def predict(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_ModelHostServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "predict": grpc.unary_unary_rpc_method_handler(
            servicer.predict,
            request_deserializer=batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Request.FromString,
            response_serializer=batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Response.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "ModelHost",
        rpc_method_handlers,
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class ModelHost:
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def predict(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/ModelHost/predict",
            batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Request.SerializeToString,
            batch__inference_dot_aio_dot_remote__model__host_dot_model__host__pb2.Response.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
