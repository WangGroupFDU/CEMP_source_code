import torch
from torch import nn
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, degree
from torch_geometric.nn import global_mean_pool

from crystals.DefaultElement import DEFAULT_ELEMENTS

num_atom_type = len(DEFAULT_ELEMENTS)
num_bond_type = 100

class GCNLayer(MessagePassing):
    def __init__(self, in_channels, out_channels):
        super(GCNLayer, self).__init__(aggr='add')
        self.linear = nn.Linear(in_channels, out_channels)
        nn.init.xavier_uniform_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

    def forward(self, x, edge_index, edge_attr):
        edge_index, edge_attr = add_self_loops(edge_index, edge_attr=edge_attr, fill_value=0)
        row, col = edge_index
        deg = degree(col, x.size(0), dtype=x.dtype)
        deg_inv_sqrt = deg.pow(-0.5)
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]
        x = self.linear(x)
        return self.propagate(edge_index, size=(x.size(0), x.size(0)), x=x, norm=norm, edge_attr=edge_attr)

    def message(self, x_j, edge_attr, norm):
        return norm.view(-1, 1) * (x_j + edge_attr)

    def update(self, aggr_out):
        return aggr_out


class GCNModel(nn.Module):
    def __init__(self, hidden_dim=100, out_dim=64, num_layers=10, dropout=0.1):
        super(GCNModel, self).__init__()
        self.x_embedding = nn.Embedding(num_atom_type, hidden_dim)
        
        nn.init.xavier_uniform_(self.x_embedding.weight)

        
        self.gcn_layers = nn.ModuleList([
            GCNLayer(hidden_dim, hidden_dim) for _ in range(num_layers)
        ])

        
        self.norm_layers = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(num_layers)
        ])

        
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.ELU()

        
        self.out = nn.Sequential(nn.Linear(hidden_dim, out_dim),
                                 nn.ELU(),
                                 
                                 )
        self.out_dim = out_dim
        
    def forward(self, data):
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        x = self.x_embedding(x)

        
        for gcn_layer, norm_layer in zip(self.gcn_layers, self.norm_layers):
            x_residual = x
            x = gcn_layer(x, edge_index, edge_attr)
            x = norm_layer(x)
            x = self.activation(x)
            x = self.dropout(x)
            x = x + x_residual  

        
        x = global_mean_pool(x, batch)

        
        x = self.out(x)
        return x