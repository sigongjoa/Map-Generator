# core/shapes.py
import numpy as np
import trimesh

class Shape:
    def __init__(self, name):
        self.name = name
        self.has_collider = True  # 기본적으로 콜라이더 활성화
        
    def generate_mesh(self):
        """3D 메시 생성 - 하위 클래스에서 구현"""
        raise NotImplementedError
        
    def generate_collider(self):
        """콜라이더 데이터 생성 - 기본적으로 메시와 동일한 박스 콜라이더"""
        mesh = self.generate_mesh()
        bounds = mesh.bounds  # 메시의 경계 상자
        return {
            "type": "BoxCollider",
            "center": mesh.centroid,
            "size": bounds[1] - bounds[0]  # 최대 좌표 - 최소 좌표 = 크기
        }
        
    def export_to_obj(self, filepath):
        """OBJ 파일로 내보내기"""
        mesh = self.generate_mesh()
        mesh.export(filepath)
        
    def to_unity_format(self):
        """유니티 호환 형식으로 변환"""
        result = {
            "mesh": self.generate_mesh(),
            "collider": self.generate_collider() if self.has_collider else None
        }
        return result

class Rectangle(Shape):
    def __init__(self, width, height, depth=0.1):
        super().__init__("Rectangle")
        self.width = width
        self.height = height
        self.depth = depth
        
    def generate_mesh(self):
        # NumPy와 trimesh를 사용하여 사각형 메시 생성
        vertices, faces = self._create_box_mesh()
        return trimesh.Trimesh(vertices=vertices, faces=faces)
        
    def _create_box_mesh(self):
        # 사각형 메시 정점 및 페이스 생성 로직
        w, h, d = self.width / 2, self.height / 2, self.depth / 2
        
        # 정점 좌표 (8개의 모서리)
        vertices = np.array([
            [-w, -h, -d],  # 0: 좌하단 뒤
            [w, -h, -d],   # 1: 우하단 뒤
            [w, h, -d],    # 2: 우상단 뒤
            [-w, h, -d],   # 3: 좌상단 뒤
            [-w, -h, d],   # 4: 좌하단 앞
            [w, -h, d],    # 5: 우하단 앞
            [w, h, d],     # 6: 우상단 앞
            [-w, h, d]     # 7: 좌상단 앞
        ])
        
        # 삼각형 면 (각 면은 2개의 삼각형으로 구성, 총 12개 삼각형)
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # 뒷면
            [4, 7, 6], [4, 6, 5],  # 앞면
            [0, 3, 7], [0, 7, 4],  # 왼쪽면
            [1, 5, 6], [1, 6, 2],  # 오른쪽면
            [3, 2, 6], [3, 6, 7],  # 윗면
            [0, 4, 5], [0, 5, 1]   # 아랫면
        ])
        
        return vertices, faces

class Circle(Shape):
    def __init__(self, radius, depth=0.1, segments=32):
        super().__init__("Circle")
        self.radius = radius
        self.depth = depth
        self.segments = segments
        
    def generate_mesh(self):
        # 원형 메시 생성 로직
        vertices = []
        faces = []
        
        # 윗면과 아랫면 중심점
        top_center_idx = 0
        bottom_center_idx = 1
        vertices.append([0, 0, self.depth / 2])  # 윗면 중심
        vertices.append([0, 0, -self.depth / 2])  # 아랫면 중심
        
        # 원주 주변의 점들
        for i in range(self.segments):
            angle = 2 * np.pi * i / self.segments
            x = self.radius * np.cos(angle)
            y = self.radius * np.sin(angle)
            
            # 윗면 모서리
            vertices.append([x, y, self.depth / 2])
            # 아랫면 모서리
            vertices.append([x, y, -self.depth / 2])
            
            # 인덱스 계산
            top_idx = i * 2 + 2
            bottom_idx = i * 2 + 3
            next_top_idx = ((i + 1) % self.segments) * 2 + 2
            next_bottom_idx = ((i + 1) % self.segments) * 2 + 3
            
            # 윗면 삼각형
            faces.append([top_center_idx, top_idx, next_top_idx])
            
            # 아랫면 삼각형
            faces.append([bottom_center_idx, next_bottom_idx, bottom_idx])
            
            # 측면 삼각형 (2개)
            faces.append([top_idx, bottom_idx, next_bottom_idx])
            faces.append([top_idx, next_bottom_idx, next_top_idx])
        
        return trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))