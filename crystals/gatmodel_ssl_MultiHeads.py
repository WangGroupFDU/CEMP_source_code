import torch                         
from torch import nn                
import torch.nn.functional as F     
from torch_geometric.nn import MessagePassing  
from torch_geometric.utils import add_self_loops, softmax  
from torch_geometric.nn import GAT   
from torch_geometric.nn import global_mean_pool  

from crystals.DefaultElement import DEFAULT_ELEMENTS      

num_atom_type = len(DEFAULT_ELEMENTS)  
num_bond_type = 100                    


class GATMultiHeadLayer(MessagePassing):
    def __init__(self, in_channels, out_channels, num_heads=4):
        
        super(GATMultiHeadLayer, self).__init__(aggr='add')
        self.node_dim = 0                   
        self.in_channels = in_channels      
        self.out_channels = out_channels    
        self.num_heads = num_heads          
        
        assert out_channels % num_heads == 0, "out_channels 必须能被 num_heads 整除"
        self.head_dim = out_channels // num_heads  

        
        self.W = torch.nn.Linear(in_channels, out_channels, bias=False)
        
        self.W_edge = torch.nn.Linear(in_channels, out_channels, bias=False)

        
        self.a = torch.nn.Parameter(torch.Tensor(num_heads, 2 * self.head_dim))

        
        self.reset_parameters()

    def reset_parameters(self):
        
        torch.nn.init.xavier_uniform_(self.W.weight)
        torch.nn.init.xavier_uniform_(self.W_edge.weight)
        
        torch.nn.init.xavier_uniform_(self.a, gain=1.414)

    def forward(self, x, edge_index, edge_attr):
        
        edge_index, edge_attr = add_self_loops(edge_index, edge_attr=edge_attr, fill_value=0)

        
        x = self.W(x)
        edge_attr = self.W_edge(edge_attr)

        
        x = x.view(-1, self.num_heads, self.head_dim)            
        edge_attr = edge_attr.view(-1, self.num_heads, self.head_dim)  

        
        out = self.propagate(edge_index, size=(x.size(0), x.size(0)), x=x, edge_attr=edge_attr)
        
        out = out.view(out.size(0), -1)
        return out

    def message(self, edge_index_i, x_i, x_j, edge_attr, size_i):
        
        
        
        x_ij = torch.cat([x_i, x_j + edge_attr], dim=-1)  

        
        
        alpha = (x_ij * self.a.unsqueeze(0)).sum(dim=-1)
        alpha = F.leaky_relu(alpha, 0.2)

        
        alpha_list = []
        for head in range(self.num_heads):
            alpha_head = softmax(alpha[:, head], edge_index_i, num_nodes=size_i)  
            alpha_list.append(alpha_head.unsqueeze(1))
        alpha = torch.cat(alpha_list, dim=1)  

        
        return x_j * alpha.unsqueeze(-1)

    def update(self, aggr_out):
        
        return aggr_out


class GATMultiHeadModel(nn.Module):
    def __init__(self, hidden_dim=100, out_dim=64, num_layers=6, dropout=0.1, num_heads=4):
        super(GATMultiHeadModel, self).__init__()
        self.out_dim = out_dim

        
        self.x_embedding = nn.Embedding(num_atom_type, hidden_dim)
        nn.init.xavier_uniform_(self.x_embedding.weight)

        
        self.gat_layers = nn.ModuleList([
            GATMultiHeadLayer(hidden_dim, hidden_dim, num_heads=num_heads) for _ in range(num_layers)
        ])

        
        self.norm_layers = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(num_layers)
        ])

        self.dropout = nn.Dropout(dropout)
        self.activation = nn.ELU()

        self.fc = nn.Linear(hidden_dim, out_dim)

    def forward(self, data):
        
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        x = self.x_embedding(x)
        for gat_layer, norm_layer in zip(self.gat_layers, self.norm_layers):
            x_residual = x  
            x = gat_layer(x, edge_index, edge_attr)  
            x = norm_layer(x)
            x = self.activation(x)
            x = self.dropout(x)
            x = x + x_residual
        x = global_mean_pool(x, batch)  
        x = self.fc(x)                  
        return x