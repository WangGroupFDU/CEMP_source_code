import torch
import torch.nn as nn

class GNNWithRegression_singleMLP(nn.Module):
    def __init__(self, encoder, regression_dim=1):
        super(GNNWithRegression_singleMLP, self).__init__()
        self.encoder = encoder  
        self.regression = nn.Linear(encoder.out_dim, regression_dim)

    def forward(self, data):
        features = self.encoder(data)  
        output = self.regression(features)  
        return output, features