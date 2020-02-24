import torch
import torch.nn as nn
import math
import torch.nn.functional as F


class Identity(nn.Module):
    # a dummy identity module
    def __init__(self):
        super(Identity, self).__init__()

    def forward(self, x):
        return x


class Unpool(nn.Module):
    # Unpool: 2*2 unpooling with zero padding
    def __init__(self, stride=2):
        super(Unpool, self).__init__()

        self.stride = stride

        # create kernel [1, 0; 0, 0]
        self.mask = torch.zeros(1, 1, stride, stride)
        self.mask[:, :, 0, 0] = 1

    def forward(self, x):
        assert x.dim() == 4
        num_channels = x.size(1)
        return F.conv_transpose2d(x,
                                  self.mask.detach().type_as(x).expand(num_channels, 1, -1, -1),
                                  stride=self.stride, groups=num_channels)


def weights_init(modules, type='xavier'):
    m = modules
    if isinstance(m, nn.Conv2d):
        if type == 'xavier':
            torch.nn.init.xavier_normal_(m.weight)
        elif type == 'kaiming':  # msra
            torch.nn.init.kaiming_normal_(m.weight)
        else:
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2. / n))

        if m.bias is not None:
            m.bias.data.zero_()
    elif isinstance(m, nn.ConvTranspose2d):
        if type == 'xavier':
            torch.nn.init.xavier_normal_(m.weight)
        elif type == 'kaiming':  # msra
            torch.nn.init.kaiming_normal_(m.weight)
        else:
            n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
            m.weight.data.normal_(0, math.sqrt(2. / n))

        if m.bias is not None:
            m.bias.data.zero_()
    elif isinstance(m, nn.BatchNorm2d):
        m.weight.data.fill_(1.0)
        m.bias.data.zero_()
    elif isinstance(m, nn.Linear):
        if type == 'xavier':
            torch.nn.init.xavier_normal_(m.weight)
        elif type == 'kaiming':  # msra
            torch.nn.init.kaiming_normal_(m.weight)
        else:
            m.weight.data.fill_(1.0)

        if m.bias is not None:
            m.bias.data.zero_()
    elif isinstance(m, nn.Module):
        for m in modules.children():
            if isinstance(m, nn.Conv2d):
                if type == 'xavier':
                    torch.nn.init.xavier_normal_(m.weight)
                elif type == 'kaiming':  # msra
                    torch.nn.init.kaiming_normal_(m.weight)
                else:
                    n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                    m.weight.data.normal_(0, math.sqrt(2. / n))

                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.ConvTranspose2d):
                if type == 'xavier':
                    torch.nn.init.xavier_normal_(m.weight)
                elif type == 'kaiming':  # msra
                    torch.nn.init.kaiming_normal_(m.weight)
                else:
                    n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                    m.weight.data.normal_(0, math.sqrt(2. / n))

                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1.0)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                if type == 'xavier':
                    torch.nn.init.xavier_normal_(m.weight)
                elif type == 'kaiming':  # msra
                    torch.nn.init.kaiming_normal_(m.weight)
                else:
                    m.weight.data.fill_(1.0)

                if m.bias is not None:
                    m.bias.data.zero_()


# def weights_init(m):
#     # Initialize kernel weights with Gaussian distributions
#     if isinstance(m, nn.Conv2d):
#         n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
#         m.weight.data.normal_(0, math.sqrt(2. / n))
#         if m.bias is not None:
#             m.bias.data.zero_()
#     elif isinstance(m, nn.ConvTranspose2d):
#         n = m.kernel_size[0] * m.kernel_size[1] * m.in_channels
#         m.weight.data.normal_(0, math.sqrt(2. / n))
#         if m.bias is not None:
#             m.bias.data.zero_()
#     elif isinstance(m, nn.BatchNorm2d):
#         m.weight.data.fill_(1)
#         m.bias.data.zero_()

def conv(in_channels, out_channels, kernel_size):
    padding = (kernel_size - 1) // 2
    assert 2 * padding == kernel_size - 1, "parameters incorrect. kernel={}, padding={}".format(kernel_size, padding)
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size, stride=1, padding=padding, bias=False),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    )


def depthwise(in_channels, kernel_size):
    padding = (kernel_size - 1) // 2  # Maintain resolution
    assert 2 * padding == kernel_size - 1, "parameters incorrect. kernel={}, padding={}".format(kernel_size, padding)
    return nn.Sequential(
        nn.Conv2d(in_channels, in_channels, kernel_size, stride=1, padding=padding, bias=False, groups=in_channels),
        nn.BatchNorm2d(in_channels),
        nn.ReLU(inplace=True),
    )


def pointwise(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=False),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    )


def convt(in_channels, out_channels, kernel_size):
    stride = 2
    padding = (kernel_size - 1) // 2
    output_padding = kernel_size % 2
    assert -2 - 2 * padding + kernel_size + output_padding == 0, "deconv parameters incorrect"  # k must be odd
    return nn.Sequential(  # Double the resolution
        nn.ConvTranspose2d(in_channels, out_channels, kernel_size,
                           stride, padding, output_padding, bias=False),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    )


def convt_dw(channels, kernel_size):
    stride = 2
    padding = (kernel_size - 1) // 2
    output_padding = kernel_size % 2
    assert -2 - 2 * padding + kernel_size + output_padding == 0, "deconv parameters incorrect"
    return nn.Sequential(
        nn.ConvTranspose2d(channels, channels, kernel_size,
                           stride, padding, output_padding, bias=False, groups=channels),
        nn.BatchNorm2d(channels),
        nn.ReLU(inplace=True),
    )

def deconv(in_channels,out_channels,kernel_size=5,output_size=None):
    modules = [convt_dw(in_channels, kernel_size),pointwise(in_channels, out_channels)]
    if output_size:
        modules.append(nn.UpsamplingNearest2d(size=output_size))
    return nn.Sequential(*modules)

def upconv(in_channels, out_channels, kernel_size=5,output_size=None):
    # Unpool then conv maintaining resolution

    modules =[
        Unpool(2),
        nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=1, padding=2, bias=False),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(),
    ]
    if output_size:
        modules.append(nn.UpsamplingNearest2d(size=output_size))
    return nn.Sequential(*modules)


class upproj(nn.Module):
    # UpProj module has two branches, with a Unpool at the start and a ReLu at the end
    #   upper branch: 5*5 conv -> batchnorm -> ReLU -> 3*3 conv -> batchnorm
    #   bottom branch: 5*5 conv -> batchnorm

    def __init__(self, in_channels, out_channels, output_size=None):
        super(upproj, self).__init__()
        self.unpool = Unpool(2)
        modules = [
            nn.Conv2d(in_channels, out_channels, kernel_size=5, stride=1, padding=2, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        ]
        if output_size:
            modules.append(nn.UpsamplingNearest2d(size=output_size))
        self.branch1 = nn.Sequential(*modules)

        modules = [nn.Conv2d(in_channels, out_channels, kernel_size=5, stride=1, padding=2, bias=False),
                   nn.BatchNorm2d(out_channels)
        ]
        if output_size:
            modules.append(nn.UpsamplingNearest2d(size=output_size))
        self.branch2 = nn.Sequential(*modules)

    def forward(self, x):
        x = self.unpool(x)
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        return F.relu(x1 + x2)


class shuffle_conv(nn.Module):
    def __init__(self, in_channels, out_channels,output_size=None):
        super(shuffle_conv, self).__init__()
        modules = [depthwise(in_channels, 5),pointwise(in_channels, out_channels)]
        if output_size:
            modules.append(nn.UpsamplingNearest2d(size=output_size))
        self.conv = nn.Sequential(
            *modules
        )

    def forward(self, x):
        x = F.pixel_shuffle(x, upscale_factor=2)
        return self.conv(x)


class ASPD(nn.Module):
    def __init__(self, in_channels, out_channels, output_size=None):
        super(ASPD, self).__init__()
        self.aspd = [0] * 3
        for i, dilation in enumerate([1, 5, 9]):
            kernel_size = 4
            padding = ((kernel_size - 1) * dilation - 1) // 2
            modules = [nn.ConvTranspose2d(in_channels=in_channels, out_channels=out_channels,
                                          kernel_size=kernel_size, padding=padding, dilation=dilation, stride=2),
                       nn.ReLU(inplace=True)
                       ]

            if output_size:
                modules.append(nn.UpsamplingNearest2d(size=output_size))
            self.aspd[i] = nn.Sequential(*modules)

            # self.aspd[i].apply(weights_init)
        self.concat_process = nn.Sequential(
            nn.Dropout2d(p=0.5),
            nn.Conv2d(out_channels * 3, out_channels, 1),
            nn.ReLU(inplace=True)
        )
        # self.concat_process.apply(weights_init)
        weights_init(self.modules(), type='xavier')

    def forward(self, x):
        outputs = []
        for i, layer in enumerate(self.aspd):
            outputs[i] = layer(x)
        output = torch.cat(outputs, dim=1)
        return self.concat_process(output)