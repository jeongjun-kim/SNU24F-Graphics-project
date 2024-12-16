# Animating an Object from a Single Monocular Video
SNU 24Fall graphics final project code repo


2024 Graphics Programming Final Project
프로젝트명 : Animating an object from single monocular video (8조)
학번 : 2020-16810
이름 : 이다은
학번 : 2019-16966
이름 : 김정준

├── README.md              
├── src/                   
│   ├── mesh_processing/   				
│   │   ├── 1-refinement/				
│   │   │   └── mesh_postprocessing.py			# 김정준
│   │   ├── 2-2-catmull-clark-subdivision/		
│   │   │   ├── catmull-clark-subdiv-all-geo.py		# 이다은
│   │   │   ├── catmull-clark-subdiv-all.py		# 이다은
│   │   │   ├── catmull-clark-subdiv-partial-geo.py	# 이다은
│   │   │   ├── catmull-clark-subdiv-partial.py		# 이다은
│   │   │   └── subdivision-demo.blend			
│   │   └── 3-laplace-smoothing/ 			
│   │       └── laplace-smoothing.py			# 김정준
│   ├── weighting/         
│   │   ├── distance-based-weighting.py      		# 김정준, 이다은
│   │   ├── graph-distance-filtering.py      		# 김정준
│   │   └── weight-smoothing.py      			# 김정준
│   ├── skinning/          
│   │   ├── dual-quaternion-skinning.py      		# 이다은
│   │   └── linear-blend-skinning.py      		# 이다은
│   ├── animating/            
│   │   └── keyframe_importing.py      			# 김정준
│   └── utils/             
│       ├── camera-moving.py				# 이다은    
│       ├── keyframe_exporting.py      			# 김정준
│       ├── mesh_logging_by_cpp.py      		# 김정준
│       ├── plane-threshold-selecting.py      		# 이다은
│       └── cpp/
│           ├── build/
│           │   └── mesh_processing.so			
│           └── src/
│               └── mesh_processing.cpp			# 김정준
├── submodules/            
│   ├── 2d-gaussain-splatting    			# 이다은
│   └── K-Planes   					# 김정준
└── resource/      
    ├── animation/
    │   ├── demo_ani_custom_hand.json     
    │   ├── demo_ani_dance.json    
    │   └── demo_ani_hand.json  
    ├── rig/      
    │   └── demo_rig.fbx      
    └── raw_mesh/  
        └──      


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
