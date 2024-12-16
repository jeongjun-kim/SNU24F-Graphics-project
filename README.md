# Animating an Object from a Single Monocular Video
SNU 24Fall graphics final project code repo

---
## Method

### 1. Preprocessing

#### 1.1. Asset  
We have used the **D-Nerf dataset**. You can download the dataset file from the Dropbox link:  
[Download Dataset](https://www.dropbox.com/scl/fi/cdcmkufncwcikk1dzbgb4/data.zip?rlkey=n5m21i84v2b2xk6h7qgiu8nkg&e=1&dl=0)  
Reference: [D-NeRF GitHub](https://github.com/albertpumarola/D-NeRF)

#### 1.2. K-Planes & 2D Gaussian Splatting  
The implementations for **K-Planes** and **2D Gaussian Splatting** are provided in the `submodules` folder:  
- [K-Planes Reference](https://github.com/sarafridov/K-Planes)  
- [2D Gaussian Splatting Reference](https://github.com/hbb1/2d-gaussian-splatting)

---

### 2. Mesh Processing

**Directory**: `src/mesh_processing`  

Open `resource/blender/naive_jumpingjacks.blend` and perform mesh processing in the following steps. Follow the detail instructions provided in the code.  

1. **Refinement**  
   Run: `1-refinement/mesh_postprocessing.py`  
2. **Catmull-Clark Subdivision**  
   Run: `2-catmull-clark-subdivision/catmull-clark-subdiv-partial.py`  
3. **Laplace Smoothing**  
   Run: `3-laplace-smoothing/laplace-smoothing.py`  

**Note**:  
For better understanding of the Catmull-Clark Subdivision code, you can try applying it to the demo version: `2-catmull-clark-subdivision/demo.blend`. This version simplifies the process as it only contains 8 vertices. You may also run:  
`2-catmull-clark-subdivision/catmull-clark-subdiv-all.py`

---

### 3. Weighting

**Directory**: `src/weighting`  

Open `resource/blender/rigged_jumpingjacks.blend` and perform the weighting process in the following steps. Rigging is done manually, so use the provided rig. Follow the detial instructions provided in the code.  

1. **Distance-Based Weighting**  
   Run: `distance-based-weighting.py`  
2. **Graph Distance Filtering**  
   Run: `graph-distance-filtering.py`  
3. **Weight Smoothing**  
   Run: `weight-smoothing.py`  

**Note**: If weights are incorrectly applied (e.g., arm bone weights affecting the torso), steps **2** and **3** will help resolve the issue.

---

### 4. Skinning

**Directory**: `src/skinning`  

Continue using `resource/blender/rigged_jumpingjacks.blend` and perform skinning. You can choose your preferred skinning method. Follow the detail instructions provided in the code.  

- **Linear Blend Skinning**: `linear-blend-skinning.py`  
- **Dual Quaternion Skinning**: `dual-quaternion-skinning.py`  

---

### 5. Animating

**Directory**: `src/animating`  

Continue using `resource/blender/rigged_jumpingjacks.blend` and proceed with animating. Follow the detail instructions provided in the code. Use animation keyframes on `resource/animation/`

- **Keyframe importing**: `keyframe_importing.py`  

---

## Notes
- Use Blender to visualize and verify results during each step.  
- The provided `.blend` files include sample rigs and meshes for experimentation.  
