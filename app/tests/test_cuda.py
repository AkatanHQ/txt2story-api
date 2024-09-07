import torch
print(torch.__version__)  # Ensure you're using a CUDA-enabled PyTorch version
print(torch.cuda.is_available())  # This should return True
print(torch.cuda.current_device())  # This shows the current CUDA device
