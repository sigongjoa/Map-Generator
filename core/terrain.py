# core/terrain.py
import numpy as np
import trimesh
import math

class Terrain:
    def __init__(self, width=100, length=100, resolution=1.0, height_scale=10.0):
        """
        지형 생성 및 편집 클래스
        
        Args:
            width (float): 지형의 너비 (X축)
            length (float): 지형의 길이 (Z축)
            resolution (float): 지형 격자의 해상도 (1.0 = 1미터당 1격자)
            height_scale (float): 높이 스케일 (10.0 = 최대 10미터 높이)
        """
        self.width = width
        self.length = length
        self.resolution = resolution
        self.height_scale = height_scale
        
        # 격자 포인트 수 계산
        self.grid_width = int(width * resolution) + 1
        self.grid_length = int(length * resolution) + 1
        
        # 높이맵 초기화 (모든 값 0)
        self.heightmap = np.zeros((self.grid_width, self.grid_length))
        
        # 지형 오브젝트 (플랫폼, 경사로 등) 저장 리스트
        self.terrain_objects = []
        
        print(f"지형 생성됨: {width}x{length}, 해상도: {resolution}, 그리드 크기: {self.grid_width}x{self.grid_length}")
        print(f"높이맵 형태: {self.heightmap.shape}")

    @property
    def rows(self):
        return self.grid_length

    @property
    def cols(self):
        return self.grid_width

    @property
    def heights(self):
        return self.heightmap
    def _generate_mesh(self):
        """
        높이맵에서 3D 메시 생성
        
        Returns:
        --------
        vertices : ndarray
            정점 배열
        faces : ndarray
            면 배열
        """
        # 정점 생성
        vertices = []
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.resolution - self.width / 2
                z = row * self.resolution - self.length / 2
                y = self.heights[row, col] * self.height_scale
                vertices.append([x, y, z])
        vertices = np.array(vertices)
        
        # 면 생성
        faces = []
        for row in range(self.rows - 1):
            for col in range(self.cols - 1):
                # 각 그리드 셀은 두 개의 삼각형으로 구성
                v0 = row * self.cols + col
                v1 = row * self.cols + col + 1
                v2 = (row + 1) * self.cols + col
                v3 = (row + 1) * self.cols + col + 1
                
                # 첫 번째 삼각형
                faces.append([v0, v1, v3])
                # 두 번째 삼각형
                faces.append([v0, v3, v2])
        faces = np.array(faces)
        
        return vertices, faces
    
    def update_mesh(self):
        """
        높이맵이 변경된 후 메시 업데이트
        """
        vertices, faces = self._generate_mesh()
        self.vertices = vertices
        self.faces = faces
        
        # 메시 속성 업데이트
        self._cache.clear()
        self.process()
    
    def get_height_at_point(self, x, z):
        """
        특정 위치(x, z)의 높이값 반환
        
        Args:
            x (float): X 좌표
            z (float): Z 좌표
            
        Returns:
            float: 해당 위치의 높이값
        """
        # 좌표를 그리드 인덱스로 변환
        grid_x = int((x + self.width / 2) * self.resolution)
        grid_z = int((z + self.length / 2) * self.resolution)
        
        # 그리드 범위 내에 있는지 확인 (rows/cols 대신 grid_width/grid_length 사용)
        if 0 <= grid_x < self.grid_width and 0 <= grid_z < self.grid_length:
            return self.heightmap[grid_x, grid_z]
        else:
            return 0

    def modify_height(self, x, z, brush_size, strength, add=True):
        """
        특정 위치 주변의 높이를 수정
        
        Args:
            x (float): 중심 X 좌표
            z (float): 중심 Z 좌표
            brush_size (float): 브러시 크기 (반경)
            strength (float): 높이 변경 강도 (0.0 ~ 1.0)
            add (bool): True면 높이기, False면 낮추기
        """
        # 중심점 그리드 좌표 계산
        center_x = int((x + self.width / 2) * self.resolution)
        center_z = int((z + self.length / 2) * self.resolution)
        
        # 브러시 크기(반경)를 그리드 단위로 변환
        grid_radius = int(brush_size * self.resolution)
        
        # 영향을 받는 그리드 범위 계산
        min_x = max(0, center_x - grid_radius)
        max_x = min(self.grid_width - 1, center_x + grid_radius)
        min_z = max(0, center_z - grid_radius)
        max_z = min(self.grid_length - 1, center_z + grid_radius)
        
        # 브러시 강도 조정 (0.01 ~ 0.5 범위로)
        adjusted_strength = strength * 0.1
        
        # 해당 영역 내의 모든 그리드 포인트에 대해
        for grid_x in range(min_x, max_x + 1):
            for grid_z in range(min_z, max_z + 1):
                # 중심점과의 거리 계산
                distance = math.sqrt((grid_x - center_x)**2 + (grid_z - center_z)**2)
                
                # 브러시 범위 내에 있는 경우
                if distance <= grid_radius:
                    # 거리에 따른 강도 계산 (중심에서 멀어질수록 강도 감소)
                    falloff = 1.0 - (distance / grid_radius)
                    effect = adjusted_strength * falloff
                    
                    # 높이값 수정
                    if add:
                        self.heightmap[grid_x, grid_z] += effect
                    else:
                        self.heightmap[grid_x, grid_z] -= effect
                    
                    # 높이값 범위 제한 (0 ~ height_scale)
                    self.heightmap[grid_x, grid_z] = max(0, min(self.height_scale, self.heightmap[grid_x, grid_z]))

        
    def flatten_area(self, x, z, brush_size):
        """
        특정 영역을 평탄화 (선택된 높이로 설정)
        
        Args:
            x (float): 중심 X 좌표
            z (float): 중심 Z 좌표
            brush_size (float): 브러시 크기 (반경)
        """
        # 중심점 그리드 좌표 계산
        center_x = int((x + self.width / 2) * self.resolution)
        center_z = int((z + self.length / 2) * self.resolution)
        
        # 중심점의 현재 높이를 기준으로 함
        target_height = self.heightmap[center_x, center_z]
        
        # 브러시 크기(반경)를 그리드 단위로 변환
        grid_radius = int(brush_size * self.resolution)
        
        # 영향을 받는 그리드 범위 계산
        min_x = max(0, center_x - grid_radius)
        max_x = min(self.grid_width - 1, center_x + grid_radius)
        min_z = max(0, center_z - grid_radius)
        max_z = min(self.grid_length - 1, center_z + grid_radius)
        
        # 해당 영역 내의 모든 그리드 포인트에 대해
        for grid_x in range(min_x, max_x + 1):
            for grid_z in range(min_z, max_z + 1):
                # 중심점과의 거리 계산
                distance = math.sqrt((grid_x - center_x)**2 + (grid_z - center_z)**2)
                
                # 브러시 범위 내에 있는 경우
                if distance <= grid_radius:
                    # 거리에 따른 가중치 계산 (중심에서 멀어질수록 영향 감소)
                    falloff = 1.0 - (distance / grid_radius)**2
                    
                    # 현재 높이와 타겟 높이 간 보간
                    self.heightmap[grid_x, grid_z] = (
                        self.heightmap[grid_x, grid_z] * (1 - falloff) + 
                        target_height * falloff
                    )
    
    def add_ramp(self, start_x, start_z, end_x, end_z, width, start_height, end_height):
        """
        경사로 추가
        
        Parameters:
        -----------
        start_x, start_z : float
            시작점 좌표
        end_x, end_z : float
            끝점 좌표
        width : float
            경사로 너비
        start_height, end_height : float
            시작과 끝의 높이
        """
        # 방향 벡터 계산
        dx = end_x - start_x
        dz = end_z - start_z
        length = math.sqrt(dx ** 2 + dz ** 2)
        
        if length == 0:
            return
            
        # 단위 방향 벡터
        dx /= length
        dz /= length
        
        # 수직 벡터 (경사로 너비 방향)
        nx = -dz
        nz = dx
        
        # 경사로 경계
        half_width = width / 2
        
        # 영향을 받는 그리드 범위 계산
        min_x = min(start_x - half_width, end_x - half_width)
        max_x = max(start_x + half_width, end_x + half_width)
        min_z = min(start_z - half_width, end_z - half_width)
        max_z = max(start_z + half_width, end_z + half_width)
        
        min_col = max(0, int((min_x + self.width / 2) / self.resolution))
        max_col = min(self.cols - 1, int((max_x + self.width / 2) / self.resolution))
        min_row = max(0, int((min_z + self.length / 2) / self.resolution))
        max_row = min(self.rows - 1, int((max_z + self.length / 2) / self.resolution))
        
        # 각 그리드 포인트에 대해 높이 수정
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                # 그리드 포인트의 월드 좌표
                x = col * self.resolution - self.width / 2
                z = row * self.resolution - self.length / 2
                
                # 선에 대한 투영 계산
                t = ((x - start_x) * dx + (z - start_z) * dz) / length
                
                # 선분 외부는 무시
                if t < 0 or t > 1:
                    continue
                    
                # 투영점 계산
                proj_x = start_x + t * (end_x - start_x)
                proj_z = start_z + t * (end_z - start_z)
                
                # 투영점과의 거리 계산
                dist = math.sqrt((x - proj_x) ** 2 + (z - proj_z) ** 2)
                
                # 경사로 너비 내에 있는 경우에만 수정
                if dist <= half_width:
                    # 가중치 계산 (가장자리에 가까울수록 원래 높이에 가깝게)
                    weight = 1.0 - (dist / half_width) ** 2
                    
                    # t값에 따른 높이 보간
                    ramp_height = start_height * (1 - t) + end_height * t
                    
                    # 원래 높이와 보간
                    original_height = self.heights[row, col]
                    self.heights[row, col] = original_height * (1 - weight) + ramp_height * weight
        
        # 메시 업데이트
        self.update_mesh()
    
    def add_platform(self, center_x, center_z, width, length, height):
        """
        평평한 플랫폼 추가
        
        Args:
            center_x (float): 중심 X 좌표
            center_z (float): 중심 Z 좌표
            width (float): 플랫폼 너비 (X축)
            length (float): 플랫폼 길이 (Z축)
            height (float): 플랫폼 높이
        """
        # 플랫폼의 모서리 좌표 계산
        half_width = width / 2
        half_length = length / 2
        
        min_x = center_x - half_width
        max_x = center_x + half_width
        min_z = center_z - half_length
        max_z = center_z + half_length
        
        # 그리드 좌표로 변환
        min_col = max(0, int((min_x + self.width / 2) * self.resolution))
        max_col = min(self.cols - 1, int((max_x + self.width / 2) * self.resolution))
        min_row = max(0, int((min_z + self.length / 2) * self.resolution))
        max_row = min(self.rows - 1, int((max_z + self.length / 2) * self.resolution))
        
        # 플랫폼 정보 저장
        platform_object = {
            "type": "platform",
            "center": (center_x, height, center_z),
            "width": width,
            "length": length
        }
        self.terrain_objects.append(platform_object)
        
        # 플랫폼 영역을 높이맵에 적용
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                # 그리드 포인트의 실제 월드 좌표
                x = (col / self.resolution) - (self.width / 2)
                z = (row / self.resolution) - (self.length / 2)
                
                # 가장자리에서 페이드 효과
                dx = abs(x - center_x) / half_width
                dz = abs(z - center_z) / half_length
                
                # 플랫폼 내부에 있는 경우
                if dx <= 1.0 and dz <= 1.0:
                    # 가장자리 부드럽게 처리
                    edge_factor = min(1.0, (1.0 - dx) * 5) * min(1.0, (1.0 - dz) * 5)
                    
                    # 현재 높이와 플랫폼 높이 합성
                    # 수정: heights -> heightmap
                    current_height = self.heightmap[col, row]
                    
                    # 플랫폼 높이가 현재 높이보다 높은 경우만 적용
                    if height > current_height:
                        self.heightmap[col, row] = max(
                            current_height,
                            current_height * (1 - edge_factor) + height * edge_factor
                        )
    
    def smooth_area(self, x, z, brush_size, strength):
        """
        특정 영역 스무딩 (주변 높이의 평균값으로 보간)
        
        Args:
            x (float): 중심 X 좌표
            z (float): 중심 Z 좌표
            brush_size (float): 브러시 크기 (반경)
            strength (float): 스무딩 강도 (0.0 ~ 1.0)
        """
        # 중심점 그리드 좌표 계산
        center_x = int((x + self.width / 2) * self.resolution)
        center_z = int((z + self.length / 2) * self.resolution)
        
        # 브러시 크기(반경)를 그리드 단위로 변환
        grid_radius = int(brush_size * self.resolution)
        
        # 영향을 받는 그리드 범위 계산
        min_x = max(1, center_x - grid_radius)
        max_x = min(self.grid_width - 2, center_x + grid_radius)
        min_z = max(1, center_z - grid_radius)
        max_z = min(self.grid_length - 2, center_z + grid_radius)
        
        # 현재 높이맵 복사 (원본 유지)
        heightmap_copy = self.heightmap.copy()
        
        # 해당 영역 내의 모든 그리드 포인트에 대해
        for grid_x in range(min_x, max_x + 1):
            for grid_z in range(min_z, max_z + 1):
                # 중심점과의 거리 계산
                distance = math.sqrt((grid_x - center_x)**2 + (grid_z - center_z)**2)
                
                # 브러시 범위 내에 있는 경우
                if distance <= grid_radius:
                    # 주변 8개 점의 평균 높이 계산
                    neighbors = [
                        heightmap_copy[grid_x-1, grid_z-1],
                        heightmap_copy[grid_x-1, grid_z],
                        heightmap_copy[grid_x-1, grid_z+1],
                        heightmap_copy[grid_x, grid_z-1],
                        heightmap_copy[grid_x, grid_z+1],
                        heightmap_copy[grid_x+1, grid_z-1],
                        heightmap_copy[grid_x+1, grid_z],
                        heightmap_copy[grid_x+1, grid_z+1]
                    ]
                    avg_height = sum(neighbors) / len(neighbors)
                    
                    # 거리에 따른 강도 계산 (중심에서 멀어질수록 강도 감소)
                    falloff = 1.0 - (distance / grid_radius)
                    effect = strength * falloff
                    
                    # 현재 높이와 평균 높이 간 보간
                    self.heightmap[grid_x, grid_z] = (
                        self.heightmap[grid_x, grid_z] * (1 - effect) + 
                        avg_height * effect
                    )
    
    def export_to_obj(self, filepath):
        """
        OBJ 파일로 내보내기
        """
        self.export(filepath)
    
    def generate_collider(self):
        """
        콜라이더 데이터 생성
        """
        # 지형에는 메시 콜라이더 사용
        return {
            "type": "MeshCollider",
            "convex": False,
            "vertices": self.vertices.tolist(),
            "faces": self.faces.tolist()
        }
    
    def export_heightmap(self, filepath):
        """
        현재 높이맵을 16비트 grayscale 이미지로 저장 (PNG 등)
        Unity 등에서 사용 가능
        """
        import imageio
        from PIL import Image
        import os

        # 정규화 (0~65535 범위의 16비트 이미지로)
        norm_heights = self.heights - self.heights.min()
        norm_heights = norm_heights / (self.heights.max() - self.heights.min() + 1e-6)
        heightmap_16bit = (norm_heights * 65535).astype(np.uint16)

        # 디렉토리 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 이미지 저장
        imageio.imwrite(filepath, heightmap_16bit)

    def export_heightmap(self):
        """
        높이맵 데이터 내보내기 (Unity용)
        
        Returns:
            dict: 지형 데이터 (높이맵, 크기 등)
        """
        try:
            # 디버깅 코드 추가
            print(f"Terrain.export_heightmap called")
            
            result = {
                "width": self.width,
                "length": self.length,
                "height_scale": self.height_scale,
                "resolution": self.resolution,
                "heightmap": self.heightmap.tolist(),  # NumPy 배열을 파이썬 리스트로 변환
                "terrain_objects": self.terrain_objects
            }
            
            print(f"export_heightmap completed with keys: {result.keys()}")
            return result
            
        except Exception as e:
            import traceback
            print(f"Error in export_heightmap: {str(e)}")
            print(traceback.format_exc())
            raise e

    def on_create_terrain(self):
        """지형 생성 버튼 클릭 처리"""
        # 지형 생성 매개변수 가져오기
        params = self.terrain_editor.get_terrain_params()
        
        # 디버깅 출력
        print(f"지형 생성 매개변수: {params}")
        
        # 지형 객체 생성
        self.terrain = Terrain(
            width=params["width"],
            length=params["length"],
            resolution=params["resolution"],
            height_scale=params["height_scale"]
        )
        
        # 객체 유효성 확인
        print(f"지형 객체 생성됨: {self.terrain}")
        print(f"높이맵 존재 여부: {'heightmap' in dir(self.terrain)}")
        if hasattr(self.terrain, 'heightmap'):
            print(f"높이맵 형태: {self.terrain.heightmap.shape}")
        
        # 미리보기 업데이트
        self.preview_widget.set_terrain(self.terrain)
        self.preview_widget.set_brush(True, self.terrain_editor.get_brush_size())
        self.preview_widget.update()
        
        # 상태바 메시지 업데이트
        self.st