from PIL import Image, ImageOps
import torch
import skvideo
import torchvision

transforms = torchvision.transforms.Compose([
                                torchvision.transforms.Resize(224),
                                torchvision.transforms.ToTensor(),
                                torchvision.transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
                            ])
toPILImage = torchvision.transforms.ToPILImage()
resize =torchvision.transforms.Resize(224)

def padding(image):
    w, h = image.size
    delta_w, delta_h = 0, 0
    if w > h:
        delta_w = 0
        delta_h = w - h
    elif w < h:
        delta_w = h - w
        delta_h = 0
    padding = (delta_w//2, delta_h//2, delta_w-(delta_w//2), delta_h-(delta_h//2))
    return ImageOps.expand(image, padding)

def padding_box(box):
    w = box[2] - box[0]
    h = box[3] - box[1]
    delta_w, delta_h = 0, 0
    if w > h:
        delta_w = 0
        delta_h = w - h
    elif w < h:
        delta_w = h - w
        delta_h = 0 
    
#    else:
 #       print('Video is a square!!')
    box[0] = box[0] - delta_w//2
    box[1] = box[1] - delta_h//2
    box[2] = box[2] + (delta_w-(delta_w//2))
    box[3] = box[3] + (delta_h-(delta_h//2))
    return box    

def transform_video_crop(video, points):
    video_torch = []
    for i in range(len(video)):
        frame = video[i]
        frame = toPILImage(frame)
        points = padding_box(points)
        frame = frame.crop(points)
        frame = padding(frame)
        frame = transforms(frame)
        video_torch.append(frame)

    video_torch = torch.stack(video_torch)
    video_torch = video_torch.permute(1,0,2,3)
    return video_torch

def save_transform_crop(video, points, path):
    writer = skvideo.io.FFmpegWriter(path,
                                        outputdict={'-b': '300000000'})
    for i in range(len(video)):
        frame = video[i]
        frame = frame = toPILImage(frame)
        frame = frame.crop(points)
        frame = padding(frame)
        frame = resize(frame)
        writer.writeFrame(frame)

    writer.close()

def transform_video_nocrop(video):
    video_torch = []
    for i in range(len(video)):
        frame = video[i]
        frame = toPILImage(frame)
        frame = padding(frame)
        frame = transforms(frame)
        video_torch.append(frame)

    video_torch = torch.stack(video_torch)
    video_torch = video_torch.permute(1,0,2,3)
    return video_torch

def save_transform_nocrop(video, path):
    video_out = []
    for i in range(len(video)):
        frame = video[i]
        frame = frame = toPILImage(frame)
        frame = padding(frame)
        frame = resize(frame)
        video_out.append(frame)

    writer = skvideo.io.FFmpegWriter(path,
                                        outputdict={'-b': '300000000'})
    for img in video_out:
        writer.writeFrame(img)
    writer.close()
