import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision


def joints_dict():
    joints = {
        "coco": {
            "keypoints": {
                0: "nose",
                1: "left_eye",
                2: "right_eye",
                3: "left_ear",
                4: "right_ear",
                5: "left_shoulder",
                6: "right_shoulder",
                7: "left_elbow",
                8: "right_elbow",
                9: "left_wrist",
                10: "right_wrist",
                11: "left_hip",
                12: "right_hip",
                13: "left_knee",
                14: "right_knee",
                15: "left_ankle",
                16: "right_ankle"
            },
            "skeleton": [
                # # [16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13], [6, 7], [6, 8],
                # # [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]
                # [15, 13], [13, 11], [16, 14], [14, 12], [11, 12], [5, 11], [6, 12], [5, 6], [5, 7],
                # [6, 8], [7, 9], [8, 10], [1, 2], [0, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6]
                [15, 13], [13, 11], [16, 14], [14, 12], [11, 12], [5, 11], [6, 12], [5, 6], [5, 7],
                [6, 8], [7, 9], [8, 10], [1, 2], [0, 1], [0, 2], [1, 3], [2, 4],  # [3, 5], [4, 6]
                [0, 5], [0, 6]
            ]
        },
        "mpii": {
            "keypoints": {
                0: "right_ankle",
                1: "right_knee",
                2: "right_hip",
                3: "left_hip",
                4: "left_knee",
                5: "left_ankle",
                6: "pelvis",
                7: "thorax",
                8: "upper_neck",
                9: "head top",
                10: "right_wrist",
                11: "right_elbow",
                12: "right_shoulder",
                13: "left_shoulder",
                14: "left_elbow",
                15: "left_wrist"
            },
            "skeleton": [
                # [5, 4], [4, 3], [0, 1], [1, 2], [3, 2], [13, 3], [12, 2], [13, 12], [13, 14],
                # [12, 11], [14, 15], [11, 10], # [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]
                [5, 4], [4, 3], [0, 1], [1, 2], [3, 2], [3, 6], [2, 6], [6, 7], [7, 8], [8, 9],
                [13, 7], [12, 7], [13, 14], [12, 11], [14, 15], [11, 10],
            ]
        },
    }
    return joints


def draw_points(image, points, color_palette='tab20', palette_samples=16):
    try:
        colors = np.round(
            np.array(plt.get_cmap(color_palette).colors) * 255
        ).astype(np.uint8)[:, ::-1].tolist()
    except AttributeError:  # if palette has not pre-defined colors
        colors = np.round(
            np.array(plt.get_cmap(color_palette)(np.linspace(0, 1, palette_samples))) * 255
        ).astype(np.uint8)[:, -2::-1].tolist()

    circle_size = max(1, min(image.shape[:2]) // 160)  # ToDo Shape it taking into account the size of the detection

    for i, pt in enumerate(points):
        if pt[2] > 0.5:
            image = cv2.circle(image, (int(pt[1]), int(pt[0])), circle_size, tuple(colors[i % len(colors)]), -1)

    return image


def draw_skeleton(image, points, skeleton, color_palette='Set2', palette_samples=8, person_index=0):
    try:
        colors = np.round(
            np.array(plt.get_cmap(color_palette).colors) * 255
        ).astype(np.uint8)[:, ::-1].tolist()
    except AttributeError:  # if palette has not pre-defined colors
        colors = np.round(
            np.array(plt.get_cmap(color_palette)(np.linspace(0, 1, palette_samples))) * 255
        ).astype(np.uint8)[:, -2::-1].tolist()

    for i, joint in enumerate(skeleton):
        pt1, pt2 = points[joint]
        if pt1[2] > 0.5 and pt2[2] > 0.5:
            image = cv2.line(
                image, (int(pt1[1]), int(pt1[0])), (int(pt2[1]), int(pt2[0])),
                tuple(colors[person_index % len(colors)]), 2
            )

    return image


def draw_points_and_skeleton(image, points, skeleton, points_color_palette='tab20', points_palette_samples=16,
                             skeleton_color_palette='Set2', skeleton_palette_samples=8, person_index=0):
    image = draw_skeleton(image, points, skeleton, color_palette=skeleton_color_palette,
                          palette_samples=skeleton_palette_samples, person_index=person_index)
    image = draw_points(image, points, color_palette=points_color_palette, palette_samples=points_palette_samples)
    return image


def save_images(images, target, joint_target, output, joint_output, joint_visibility, summary_writer=None, step=0,
                prefix=''):
    # Input images with gt
    images_ok = images.detach().clone()
    images_ok[:, 0].mul_(0.229).add_(0.485)
    images_ok[:, 1].mul_(0.224).add_(0.456)
    images_ok[:, 2].mul_(0.225).add_(0.406)
    for i in range(images.shape[0]):
        joints = joint_target[i] * 4.
        joints_vis = joint_visibility[i]

        for joint, joint_vis in zip(joints, joints_vis):
            if joint_vis[0]:
                a = int(joint[1].item())
                b = int(joint[0].item())
                # images_ok[i][:, a-1:a+1, b-1:b+1] = torch.tensor([1, 0, 0])
                images_ok[i][0, a - 1:a + 1, b - 1:b + 1] = 1
                images_ok[i][1:, a - 1:a + 1, b - 1:b + 1] = 0
    grid_gt = torchvision.utils.make_grid(images_ok, nrow=int(images_ok.shape[0] ** 0.5), padding=2, normalize=False)
    if summary_writer is not None:
        summary_writer.add_image(prefix + 'images', grid_gt, global_step=step)

    # Input images with prediction
    images_ok = images.detach().clone()
    images_ok[:, 0].mul_(0.229).add_(0.485)
    images_ok[:, 1].mul_(0.224).add_(0.456)
    images_ok[:, 2].mul_(0.225).add_(0.406)
    for i in range(images.shape[0]):
        joints = joint_output[i] * 4.
        joints_vis = joint_visibility[i]

        for joint, joint_vis in zip(joints, joints_vis):
            if joint_vis[0]:
                a = int(joint[1].item())
                b = int(joint[0].item())
                # images_ok[i][:, a-1:a+1, b-1:b+1] = torch.tensor([1, 0, 0])
                images_ok[i][0, a - 1:a + 1, b - 1:b + 1] = 1
                images_ok[i][1:, a - 1:a + 1, b - 1:b + 1] = 0
    grid_pred = torchvision.utils.make_grid(images_ok, nrow=int(images_ok.shape[0] ** 0.5), padding=2, normalize=False)
    if summary_writer is not None:
        summary_writer.add_image(prefix + 'predictions', grid_pred, global_step=step)


    return grid_gt, grid_pred
