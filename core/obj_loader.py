# core/obj_loader.py
class OBJLoader:
    @staticmethod
    def load(filepath):
        """
        OBJ 파일을 로드하여 메시 데이터로 변환
        
        Args:
            filepath (str): OBJ 파일 경로
            
        Returns:
            dict: 메시 데이터 (정점, 삼각형, UV 등)
        """
        vertices = []
        normals = []
        uvs = []
        faces = []
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # 빈 줄 무시
                    if not line:
                        continue
                    
                    # 주석 무시
                    if line.startswith('#'):
                        continue
                    
                    values = line.split()
                    
                    # 정점 (v)
                    if values[0] == 'v':
                        vertices.append((float(values[1]), float(values[2]), float(values[3])))
                    
                    # 정점 노멀 (vn)
                    elif values[0] == 'vn':
                        normals.append((float(values[1]), float(values[2]), float(values[3])))
                    
                    # 텍스처 좌표 (vt)
                    elif values[0] == 'vt':
                        # OBJ 파일의 vt는 (u, v, [w]) 형식이지만, w는 선택적이므로 무시
                        uvs.append((float(values[1]), float(values[2])))
                    
                    # 면 (f)
                    elif values[0] == 'f':
                        face = []
                        for v in values[1:]:
                            # f v/vt/vn 형식 처리
                            face_vertex = v.split('/')
                            
                            # OBJ 인덱스는 1부터 시작하므로 0부터 시작하도록 변환
                            # 정점 인덱스
                            v_idx = int(face_vertex[0]) - 1
                            
                            # 텍스처 좌표 인덱스 (있는 경우)
                            vt_idx = -1
                            if len(face_vertex) > 1 and face_vertex[1]:
                                vt_idx = int(face_vertex[1]) - 1
                            
                            # 노멀 인덱스 (있는 경우)
                            vn_idx = -1
                            if len(face_vertex) > 2 and face_vertex[2]:
                                vn_idx = int(face_vertex[2]) - 1
                            
                            face.append((v_idx, vt_idx, vn_idx))
                        
                        faces.append(face)
            
            # 메시 데이터 구성
            # 간단한 구현을 위해 모든 면을 삼각형화 (삼각형이 아닌 면 처리)
            triangles = []
            for face in faces:
                if len(face) == 3:
                    # 이미 삼각형
                    triangles.append((face[0][0], face[1][0], face[2][0]))
                else:
                    # 삼각형화 (팬 방식)
                    for i in range(1, len(face) - 1):
                        triangles.append((face[0][0], face[i][0], face[i+1][0]))
            
            # 텍스처 좌표 및 노멀이 없는 경우 처리
            if not uvs:
                # 임시 UV 좌표 생성
                uvs = [(0, 0)] * len(vertices)
            
            if not normals:
                # 임시 노멀 생성
                normals = [(0, 1, 0)] * len(vertices)
            
            return {
                "vertices": vertices,
                "triangles": triangles,
                "uvs": uvs,
                "normals": normals
            }
            
        except Exception as e:
            print(f"OBJ 파일 로드 오류: {str(e)}")
            return None