import torch
from torch.utils import data

import numpy as np
import os

class Dataset(data.Dataset):
    'Characterizes a dataset for PyTorch'
    def __init__(self, dir_pose, dir_video, n_frames, downsample_pose=1, downsample_video=1):
        self.dir_pose = dir_pose
        self.dir_video = dir_video

        self.list_poses = []
        self.list_videos = []
        self.list_labels = []

        self.n_frames = n_frames
        self.downsample_pose = downsample_pose
        self.downsample_video = downsample_video

        self.classes, self.class_to_idx, self.idx_to_class = self._find_classes(dir_pose, dir_video)

        #crea lista video e label leggendo dalla directory root
        for Afolder in self.class_to_idx.keys():
            Afolder_pose = os.path.join(dir_pose, Afolder)
            Afolder_video = os.path.join(dir_video, Afolder)

            pose_files = sorted([f.path for f in os.scandir(Afolder_pose)])
            video_files = sorted([f.path for f in os.scandir(Afolder_video)])

            #sanity check
            if len(pose_files) != len(video_files):
                raise Exception("error _init__ myDataset")
            for i in range(len(pose_files)):
                pose_file = pose_files[i]
                video_file = video_files[i]
                #sanity check
                pose_name = pose_file.split(".")[0]
                video_name  = video_file.split(".")[0]
                if pose_name != video_name:
                    raise Exception("error _init__ myDataset in files name")
                self.list_poses.append(pose_file)
                self.list_videos.append(video_file)
                self.list_labels.append(self.class_to_idx[Afolder])
   
                
    def _find_classes(self, dir_pose, dir_video):
        classes_poses = sorted([d.name for d in os.scandir(dir_pose) if d.is_dir()])
        classes_videos = sorted([d.name for d in os.scandir(dir_video) if d.is_dir()])
        #sanity check
        class_to_idx = {}
        idx_to_class = {}
        if len(classes_poses) != len(classes_videos):
            raise Exception('errore in _find_classes')
        for i in range(len(classes_poses)):
            if classes_poses[i] == classes_videos[i]:
                class_to_idx[classes_poses[i]] = i
                idx_to_class[i] = classes_poses[i]
            else:
                raise Exception('errore in _find_classes')

        classes = classes_poses
        return classes, class_to_idx, idx_to_class

    def _campionamento(self, pose, campionamento):
        depth = pose.shape[1]
        if(campionamento == 1):
            return pose
        if(depth // self.n_frames >= campionamento):
            return pose[:,::campionamento,:,:]
        else:
            return self._campionamento(pose, campionamento -1)

    def _center(self, data):
        center = data.shape[1] // 2
        frame = self.n_frames // 2
        return data[:,center-frame:center+frame,:,:]

    def auto_pading(self, data):
        size = self.n_frames
        C, T, H, W = data.shape
        if T < size:
            begin = (size - T) // 2
            data_padded = torch.zeros((C, size, H, W))
            data_padded[:, begin:begin + T, :, :] = data
            return data_padded
        else:
            return data

    def __len__(self):
        'Denotes the total number of samples'
        return len(self.list_labels)

    def __getitem__(self, index):
        'Generates one sample of data'
        pose = self.list_poses[index]
        pose_numpy = np.load(pose)
        pose_torch = torch.from_numpy(pose_numpy)
        pose_padded = self.auto_pading(pose_torch)
        X_pose = self._campionamento(pose_padded, self.downsample_pose)
        X_pose = self._center(X_pose)

        video = self.list_videos[index]
        video_torch = torch.load(video)
        video_padded = self.auto_pading(video_torch)
        X_video = self._campionamento(video_padded, self.downsample_video)
        X_video = self._center(X_video)

        label = self.list_labels[index]

        return X_pose.float(), X_video, label

    def bincount(self):
        return torch.bincount(torch.tensor(self.list_labels))

    def print(self):
        print("Dataset:")
        print("\t", self.dir_pose)
        print("\t", self.dir_video)
        print("Numero Azioni", self.__len__())
        print("Classes:", self.classes)
        print("Classes to index:")
        for c in self.class_to_idx:
            print("Label:", c, "index:", self.class_to_idx[c])
        print("Numero di frame:", self.n_frames,)
        print("Downsample pose:", self.downsample_pose)
        print("Downsample video:", self.downsample_video)
        bins = self.bincount()
        for idx, _bin in enumerate(bins):
            print(self.idx_to_class[idx], "\t", _bin.item())


if __name__ == '__main__':
    dataset = Dataset('../Dataset/aggregorio_skeletons_numpy/basic/test', 
                        '../Dataset/aggregorio_videos_pytorch/basic/test',
                        n_frames=16, downsample_pose=1, downsample_video=2)

    dataset.print()

    loader = data.DataLoader(dataset, batch_size=32, num_workers=8, pin_memory=True)
    for poses, videos, labels in loader:
        print(poses.shape, videos.shape, labels.shape)

   