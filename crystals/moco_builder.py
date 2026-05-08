

import torch
import torch.nn as nn
import torch.nn.functional as F

class MoCo(nn.Module):

    def __init__(self, base_encoder, dim=128, K=65536, m=0.999, T=0.07, mlp=False):
        """
        dim: feature dimension (default: 128)
        K: queue size; number of negative keys (default: 65536)
        m: moco momentum of updating key encoder (default: 0.999)
        T: softmax temperature (default: 0.07)
        """
        super(MoCo, self).__init__()

        self.K = K
        self.m = m
        self.T = T

        
        self.encoder_q = base_encoder
        self.encoder_k = base_encoder

        if mlp:  
            dim_mlp = self.encoder_q.fc.weight.shape[1]

            self.encoder_q.fc = nn.Sequential(
                nn.Linear(dim_mlp, dim_mlp), nn.ReLU(), self.encoder_q.fc
            )
            self.encoder_k.fc = nn.Sequential(
                nn.Linear(dim_mlp, dim_mlp), nn.ReLU(), self.encoder_k.fc
            )

        for param_q, param_k in zip(
            self.encoder_q.parameters(), self.encoder_k.parameters()
        ):
            param_k.data.copy_(param_q.data)  
            param_k.requires_grad = False  

        for param in self.encoder_q.parameters():
            param.requires_grad = True

        
        self.register_buffer("queue", torch.randn(dim, K))
        self.queue = nn.functional.normalize(self.queue, dim=0)

        self.register_buffer("queue_ptr", torch.zeros(1, dtype=torch.long))

    @torch.no_grad()
    def _momentum_update_key_encoder(self):
        """
        Momentum update of the key encoder
        """
        for param_q, param_k in zip(
            self.encoder_q.parameters(), self.encoder_k.parameters()
        ):
            param_k.data = param_k.data * self.m + param_q.data * (1.0 - self.m)

    @torch.no_grad()
    def _dequeue_and_enqueue(self, keys):

        batch_size = keys.size(0)
        assert self.K % batch_size == 0  

        
        ptr = int(self.queue_ptr)
        self.queue[:, ptr : ptr + batch_size] = keys.T
        ptr = (ptr + batch_size) % self.K  
        self.queue_ptr[0] = ptr

    def forward(self, data_q, data_k):
        
        
        q = self.encoder_q(data_q)
        q = F.normalize(q, dim=1)
        
        with torch.no_grad():  
            self._momentum_update_key_encoder()  
            
            k = self.encoder_k(data_k)
            k = F.normalize(k, dim=1)
        
        
        
        l_pos = torch.einsum("nc,nc->n", [q, k]).unsqueeze(-1)
        
        l_neg = torch.einsum("nc,ck->nk", [q, self.queue.clone().detach()])
        
        logits = torch.cat([l_pos, l_neg], dim=1)
        
        logits /= self.T
        
        labels = torch.zeros(logits.shape[0], dtype=torch.long).to(logits.device)
        
        self._dequeue_and_enqueue(k)
        return logits, labels

