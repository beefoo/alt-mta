import numpy as np
import pyopencl as cl

def buildProgram(src):
    ctx = getContext()

    # Create queue for each kernel execution
    queue = cl.CommandQueue(ctx)

    # Kernel function instantiation
    prg = cl.Program(ctx, src).build()

    return (ctx, prg, queue)

def copyResult(queue, result, outResult):
    cl.enqueue_copy(queue, result, outResult)

def getContext():
    # Get platforms, both CPU and GPU
    plat = cl.get_platforms()
    GPUs = plat[0].get_devices(device_type=cl.device_type.GPU)
    CPU = plat[0].get_devices()

    # prefer GPUs
    if GPUs and len(GPUs) > 0:
        ctx = cl.Context(devices=GPUs)
    else:
        print "Warning: using CPU"
        ctx = cl.Context(CPU)

    return ctx

def getInBuffer(ctx, buf):
    mf = cl.mem_flags
    return cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=buf)

def getOutBuffer(ctx, size):
    mf = cl.mem_flags
    return cl.Buffer(ctx, mf.WRITE_ONLY, size)
