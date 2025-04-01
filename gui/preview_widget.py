# gui/preview_widget.py
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

class PreviewWidget(QOpenGLWidget):
    # 지형 클릭 시그널 (x, z, 버튼)
    terrain_clicked = pyqtSignal(float, float, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 메시 데이터
        self.mesh = None
        # 지형 데이터
        self.terrain = None
        
        
        # 카메라 설정
        self.camera_distance = 20
        self.camera_rotation_x = 30  # 회전 각도 (X축)
        self.camera_rotation_y = 45  # 회전 각도 (Y축)
        
        # 마우스 관련 변수
        self.last_pos = None
        self.is_rotating = False
        self.is_panning = False
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        
        # 브러시 모드 관련 변수
        self.brush_active = False
        self.brush_size = 5
        self.brush_position = None
        self.ramp_mode = False
        self.ramp_start = None
        
        # 마우스 이벤트 추적 활성화
        self.setMouseTracking(True)
        
        # OpenGL 위젯 포커스 설정
        self.setFocusPolicy(Qt.ClickFocus)
    
    def set_mesh(self, mesh):
        """메시 데이터 설정"""
        self.mesh = mesh
        self.update()
    
    def set_terrain(self, terrain):
        """지형 데이터 설정"""
        self.terrain = terrain
        self.update()
    
    def set_brush(self, active, size=5):
        """브러시 활성화/비활성화 및 크기 설정"""
        self.brush_active = active
        self.brush_size = size
        self.update()
    
    def set_ramp_mode(self, active):
        """경사로 모드 설정"""
        self.ramp_mode = active
        if not active:
            self.ramp_start = None
        self.update()
    
    def paintEvent(self, event):
        """그리기 이벤트 처리"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 배경 그리기
        painter.fillRect(self.rect(), QColor(32, 32, 40))
        
        # 그리드 그리기
        self._draw_grid(painter)
        
        # 지형 그리기
        if self.terrain:
            self._draw_terrain(painter)
        
        # 메시 그리기
        if self.mesh:
            self._draw_mesh(painter)
        
        # 브러시 그리기
        self._draw_brush(painter)
        
        # 경사로 미리보기 그리기
        if self.ramp_mode and self.ramp_start and self.brush_position:
            self._draw_ramp_preview(painter)
        
        # 정보 텍스트 그리기
        self._draw_info_text(painter)
        
        painter.end()
    
    def _draw_grid(self, painter):
        """그리드 그리기"""
        width, height = self.width(), self.height()
        
        # 그리드 간격 (10m 단위)
        grid_size = 10 * self.get_scale()
        
        # 원점 계산 (화면 중앙 + 패닝 오프셋)
        origin_x = width / 2 + self.pan_offset_x
        origin_z = height / 2 + self.pan_offset_y
        
        # 그리드 펜 설정
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        
        # 수직 그리드선
        for x in range(-50, 51, 10):
            screen_x = origin_x + x * grid_size
            painter.drawLine(int(screen_x), 0, int(screen_x), height)
        
        # 수평 그리드선
        for z in range(-50, 51, 10):
            screen_z = origin_z + z * grid_size
            painter.drawLine(0, int(screen_z), width, int(screen_z))
        
        # 축 그리기
        painter.setPen(QPen(QColor(255, 0, 0), 2))  # X축 (빨간색)
        painter.drawLine(int(origin_x), int(origin_z), int(origin_x + 5 * grid_size), int(origin_z))
        
        painter.setPen(QPen(QColor(0, 0, 255), 2))  # Z축 (파란색)
        painter.drawLine(int(origin_x), int(origin_z), int(origin_x), int(origin_z + 5 * grid_size))
    
    def _draw_terrain(self, painter):
        """지형 그리기"""
        if not self.terrain:
            return
        
        width, height = self.width(), self.height()
        
        # 스케일 및 원점 계산
        scale = self.get_scale()
        origin_x = width / 2 + self.pan_offset_x
        origin_z = height / 2 + self.pan_offset_y
        
        # 지형 격자 그리기
        painter.setPen(QPen(QColor(100, 100, 160), 1))
        
        # 높이맵 크기 - cols 대신 grid_width, rows 대신 grid_length 사용
        heightmap_width = self.terrain.grid_width
        heightmap_length = self.terrain.grid_length
        
        # 지형의 실제 크기
        terrain_width = self.terrain.width
        terrain_length = self.terrain.length
        
        # 스텝 크기 계산 (모든 격자점을 그리면 너무 많으므로)
        step = max(1, min(heightmap_width, heightmap_length) // 100)
        
        # 지형의 월드 좌표 범위
        min_x = -terrain_width / 2
        max_x = terrain_width / 2
        min_z = -terrain_length / 2
        max_z = terrain_length / 2
        
        # 간략화된 격자점 그리기
        for grid_x in range(0, heightmap_width, step):
            for grid_z in range(0, heightmap_length, step):
                # 실제 월드 좌표 계산
                x = min_x + (grid_x / (heightmap_width - 1)) * terrain_width
                z = min_z + (grid_z / (heightmap_length - 1)) * terrain_length
                y = self.terrain.heightmap[grid_x, grid_z]
                
                # 화면 좌표 변환
                screen_x = origin_x + x * scale
                screen_z = origin_z + z * scale
                
                # 높이에 따른 색상 계산
                height_ratio = y / self.terrain.height_scale
                r = int(100 + height_ratio * 155)
                g = int(100 + height_ratio * 155)
                b = int(160 - height_ratio * 60)
                
                # 작은 점 그리기
                painter.setPen(QPen(QColor(r, g, b), 2))
                painter.drawPoint(int(screen_x), int(screen_z))
        
        # 지형 오브젝트 (플랫폼, 경사로) 그리기
        for obj in self.terrain.terrain_objects:
            if obj["type"] == "platform":
                # 플랫폼 그리기
                center_x, center_y, center_z = obj["center"]
                width = obj["width"]
                length = obj["length"]
                
                # 화면 좌표 변환
                screen_x = origin_x + center_x * scale
                screen_z = origin_z + center_z * scale
                rect_width = width * scale
                rect_height = length * scale
                
                # 사각형 그리기
                painter.setPen(QPen(QColor(0, 200, 0), 2))
                painter.drawRect(
                    int(screen_x - rect_width / 2),
                    int(screen_z - rect_height / 2),
                    int(rect_width),
                    int(rect_height)
                )
                
                # 높이 텍스트 표시
                painter.setFont(QFont("Arial", 8))
                painter.drawText(
                    int(screen_x - 15),
                    int(screen_z),
                    f"H: {center_y:.1f}m"
                )
                
            elif obj["type"] == "ramp":
                # 경사로 그리기
                start_x, start_y, start_z = obj["start"]
                end_x, end_y, end_z = obj["end"]
                width = obj["width"]
                
                # 화면 좌표 변환
                start_screen_x = origin_x + start_x * scale
                start_screen_z = origin_z + start_z * scale
                end_screen_x = origin_x + end_x * scale
                end_screen_z = origin_z + end_z * scale
                
                # 선 그리기
                painter.setPen(QPen(QColor(200, 100, 0), 3))
                painter.drawLine(
                    int(start_screen_x),
                    int(start_screen_z),
                    int(end_screen_x),
                    int(end_screen_z)
                )
                
                # 화살표 그리기 (경사로 방향 표시)
                self._draw_arrow(painter, 
                            int(start_screen_x), 
                            int(start_screen_z),
                            int(end_screen_x),
                            int(end_screen_z))
                
                # 높이 텍스트 표시
                painter.setFont(QFont("Arial", 8))
                painter.drawText(
                    int(start_screen_x - 15),
                    int(start_screen_z - 10),
                    f"H1: {start_y:.1f}m"
                )
                painter.drawText(
                    int(end_screen_x - 15),
                    int(end_screen_z - 10),
                    f"H2: {end_y:.1f}m"
                )    
    def _draw_arrow(self, painter, x1, y1, x2, y2):
        """화살표 그리기 (두 점 사이)"""
        import math
        
        # 화살표 크기
        arrow_size = 10
        
        # 방향 벡터 계산
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return
            
        # 방향 벡터 정규화
        dx /= length
        dy /= length
        
        # 화살촉 위치 (끝점에서 약간 뒤로)
        arrow_x = x2 - dx * arrow_size * 0.5
        arrow_y = y2 - dy * arrow_size * 0.5
        
        # 화살촉 좌우 점 계산 (수직 벡터 사용)
        px = -dy
        py = dx
        
        left_x = arrow_x + px * arrow_size * 0.5
        left_y = arrow_y + py * arrow_size * 0.5
        right_x = arrow_x - px * arrow_size * 0.5
        right_y = arrow_y - py * arrow_size * 0.5
        
        # 화살촉 그리기
        arrow_points = [
            QPoint(x2, y2),
            QPoint(int(left_x), int(left_y)),
            QPoint(int(right_x), int(right_y))
        ]
        
        painter.setBrush(QColor(200, 100, 0))
        painter.drawPolygon(arrow_points)
    
    def _draw_mesh(self, painter):
        """메시 그리기"""
        if not self.mesh:
            return
            
        # TODO: OpenGL을 사용한 3D 메시 렌더링 구현
        # 지금은 간단히 와이어프레임으로 표시
        
        width, height = self.width(), self.height()
        
        # 스케일 및 원점 계산
        scale = self.get_scale()
        origin_x = width / 2 + self.pan_offset_x
        origin_z = height / 2 + self.pan_offset_y
        
        # 와이어프레임 펜 설정
        painter.setPen(QPen(QColor(0, 200, 200), 1))
        
        # 삼각형 그리기
        triangles = self.mesh["triangles"]
        vertices = self.mesh["vertices"]
        
        for triangle in triangles:
            # 삼각형의 세 점
            v1 = vertices[triangle[0]]
            v2 = vertices[triangle[1]]
            v3 = vertices[triangle[2]]
            
            # 화면 좌표 변환
            screen_x1 = origin_x + v1[0] * scale
            screen_z1 = origin_z + v1[2] * scale
            screen_x2 = origin_x + v2[0] * scale
            screen_z2 = origin_z + v2[2] * scale
            screen_x3 = origin_x + v3[0] * scale
            screen_z3 = origin_z + v3[2] * scale
            
            # 삼각형 그리기
            painter.drawLine(int(screen_x1), int(screen_z1), int(screen_x2), int(screen_z2))
            painter.drawLine(int(screen_x2), int(screen_z2), int(screen_x3), int(screen_z3))
            painter.drawLine(int(screen_x3), int(screen_z3), int(screen_x1), int(screen_z1))
    
    def _draw_brush(self, painter):
        """브러시 그리기"""
        if not self.brush_active or not self.brush_position:
            return
            
        width, height = self.width(), self.height()
        
        # 스케일 및 원점 계산
        scale = self.get_scale()
        origin_x = width / 2 + self.pan_offset_x
        origin_z = height / 2 + self.pan_offset_y
        
        # 브러시 위치를 화면 좌표로 변환
        screen_x = origin_x + self.brush_position[0] * scale
        screen_z = origin_z + self.brush_position[2] * scale
        
        # 브러시 반경
        brush_radius = self.brush_size * scale
        
        # 브러시 원 그리기
        painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
        painter.drawEllipse(
            int(screen_x - brush_radius),
            int(screen_z - brush_radius),
            int(brush_radius * 2),
            int(brush_radius * 2)
        )
        
        # 브러시 중심점 그리기
        painter.setPen(QPen(QColor(255, 255, 0), 4))
        painter.drawPoint(int(screen_x), int(screen_z))
    
    def _draw_ramp_preview(self, painter):
        """경사로 미리보기 그리기"""
        if not self.ramp_start or not self.brush_position:
            return
            
        width, height = self.width(), self.height()
        
        # 스케일 및 원점 계산
        scale = self.get_scale()
        origin_x = width / 2 + self.pan_offset_x
        origin_z = height / 2 + self.pan_offset_y
        
        # 시작점과 현재 위치를 화면 좌표로 변환
        start_x = origin_x + self.ramp_start[0] * scale
        start_z = origin_z + self.ramp_start[2] * scale
        
        current_x = origin_x + self.brush_position[0] * scale
        current_z = origin_z + self.brush_position[2] * scale
        
        # 선 그리기
        painter.setPen(QPen(QColor(255, 200, 0), 2, Qt.DashLine))
        painter.drawLine(int(start_x), int(start_z), int(current_x), int(current_z))
        
        # 시작점 표시
        painter.setPen(QPen(QColor(255, 200, 0), 6))
        painter.drawPoint(int(start_x), int(start_z))
        
        # 텍스트 표시
        painter.setFont(QFont("Arial", 8))
        
        # 시작점 레이블
        painter.drawText(int(start_x + 10), int(start_z), "시작점")
        
        # 현재 점 레이블
        painter.drawText(int(current_x + 10), int(current_z), "끝점")
        
        # 거리 계산 및 표시
        import math
        dx = self.brush_position[0] - self.ramp_start[0]
        dz = self.brush_position[2] - self.ramp_start[2]
        distance = math.sqrt(dx*dx + dz*dz)
        
        # 거리 표시 (중간 지점에)
        mid_x = (start_x + current_x) / 2
        mid_z = (start_z + current_z) / 2
        painter.drawText(int(mid_x), int(mid_z - 10), f"거리: {distance:.1f}m")
    
    def _draw_info_text(self, painter):
        """정보 텍스트 그리기"""
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Arial", 9))
        
        # 조작 안내
        text = [
            "마우스 좌클릭 + 드래그: 카메라 회전",
            "마우스 우클릭 + 드래그: 화면 이동",
            "마우스 휠: 확대/축소",
            "브러시 모드에서 좌클릭: 지형 수정"
        ]
        
        y = 20
        for line in text:
            painter.drawText(10, y, line)
            y += 15
        
        # 현재 마우스 위치 정보
        if self.brush_position:
            x, y, z = self.brush_position
            height = 0
            
            if self.terrain:
                try:
                    height = self.terrain.get_height_at_point(x, z)
                    
                    # 디버깅 정보 추가
                    position_text = f"X: {x:.1f}, Z: {z:.1f}, 높이: {height:.1f}m"
                    painter.drawText(10, self.height() - 10, position_text)
                    
                except Exception as e:
                    # 오류가 발생한 경우 대비
                    error_text = f"위치 정보 표시 오류: {str(e)}"
                    painter.drawText(10, self.height() - 10, error_text)
                    print(f"Error in _draw_info_text: {str(e)}")
            else:
                position_text = f"X: {x:.1f}, Z: {z:.1f}"
                painter.drawText(10, self.height() - 10, position_text)
                
    def get_scale(self):
        """현재 뷰의 스케일 계산"""
        # 기본 스케일 및 거리에 따른 조정
        base_scale = 5.0
        distance_factor = 20 / max(1, self.camera_distance)
        return base_scale * distance_factor
    
    def screen_to_world(self, screen_x, screen_y):
        """화면 좌표를 월드 좌표로 변환"""
        # 원점 및 스케일 계산
        origin_x = self.width() / 2 + self.pan_offset_x
        origin_z = self.height() / 2 + self.pan_offset_y
        scale = self.get_scale()
        
        # 월드 좌표 계산
        world_x = (screen_x - origin_x) / scale
        world_z = (screen_y - origin_z) / scale
        
        return world_x, 0, world_z
    
    def mousePressEvent(self, event):
        """마우스 버튼 누름 이벤트"""
        self.last_pos = event.pos()
        
        if event.button() == Qt.LeftButton:
            if self.brush_active and self.terrain:
                # 브러시 모드에서 지형 수정
                world_pos = self.screen_to_world(event.x(), event.y())
                self.brush_position = world_pos
                
                # 지형 클릭 시그널 발생 (월드 좌표, 버튼)
                self.terrain_clicked.emit(world_pos[0], world_pos[2], 1)
                
                self.update()
            else:
                # 카메라 회전 모드
                self.is_rotating = True
        
        elif event.button() == Qt.RightButton:
            # 화면 이동 모드
            self.is_panning = True
    
    def mouseReleaseEvent(self, event):
        """마우스 버튼 해제 이벤트"""
        if event.button() == Qt.LeftButton:
            self.is_rotating = False
            
            if self.brush_active and self.terrain:
                # 브러시 모드에서 마우스 업 시 시그널 발생
                world_pos = self.screen_to_world(event.x(), event.y())
                self.terrain_clicked.emit(world_pos[0], world_pos[2], 0)
        
        elif event.button() == Qt.RightButton:
            self.is_panning = False
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if self.last_pos is None:
            self.last_pos = event.pos()
            return
            
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        
        if self.is_rotating:
            # 카메라 회전
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x += dy * 0.5
            
            # X 회전 범위 제한 (천정/바닥 뚫림 방지)
            self.camera_rotation_x = max(10, min(80, self.camera_rotation_x))
            
            self.update()
            
        elif self.is_panning:
            # 화면 이동
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            
            self.update()
        
        # 브러시 위치 업데이트
        if self.brush_active:
            world_pos = self.screen_to_world(event.x(), event.y())
            self.brush_position = world_pos
            
            if self.terrain and (event.buttons() & Qt.LeftButton):
                # 드래그 중에도 지형 수정 (연속적인 브러시 효과)
                self.terrain_clicked.emit(world_pos[0], world_pos[2], 1)
            
            self.update()
        
        self.last_pos = event.pos()
    
    def wheelEvent(self, event):
        """마우스 휠 이벤트 (확대/축소)"""
        delta = event.angleDelta().y()
        
        # 확대/축소 속도 조정
        zoom_speed = 0.1
        
        self.camera_distance -= delta * zoom_speed
        
        # 거리 범위 제한
        self.camera_distance = max(5, min(100, self.camera_distance))
        
        self.update()