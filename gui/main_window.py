# gui/main_window.py (완전히 업데이트된 버전)
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QGroupBox, QFormLayout, QDoubleSpinBox, 
                            QCheckBox, QFileDialog, QMessageBox, QLabel, QAction,
                            QTabWidget, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from core.shapes import Rectangle, Circle
from core.obj_loader import OBJLoader
from core.unity_exporter import UnityExporter
from core.terrain import Terrain
from gui.preview_widget import PreviewWidget
from gui.terrain_editor import TerrainEditorWidget
import json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Editor")
        self.resize(1200, 800)
        
        self.map_width = 800
        self.map_height = 600

        # 도형 관련 변수 설정
        self.shapes = []  # 배치된 도형 목록
        self.current_shape_type = "Rectangle"  # 기본 도형
        self.is_placing = False  # 배치 모드 여부
        self.is_moving = False   # 이동 모드 여부
        self.current_shape = None  # 현재 생성 중인 도형
        self.selected_shape_index = None  # 선택된 도형 인덱스
        
        # 지형 관련 변수 설정
        self.terrain = None  # 지형 데이터
        self.ramp_start_point = None  # 경사로 시작점
        
        self._init_ui()
            
    def _init_ui(self):
        """UI 초기화"""
        # 창 기본 설정
        self.setWindowTitle("Map Editor")
        self.resize(1200, 800)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 상단 도구 모음 및 버튼 패널
        toolbar_layout = QHBoxLayout()
        
        # 도형 선택 버튼
        self.rect_btn = QPushButton("사각형")
        self.circle_btn = QPushButton("원")
        self.cylinder_btn = QPushButton("실린더")
        self.semicircle_btn = QPushButton("반원")
        
        
        # 버튼 이벤트 연결
        self.map_size_btn = QPushButton("맵 크기 조정")
        self.map_size_btn.clicked.connect(self.show_map_size_dialog)
        self.rect_btn.clicked.connect(lambda: self.on_shape_selected("Rectangle"))
        self.circle_btn.clicked.connect(lambda: self.on_shape_selected("Circle"))
        self.cylinder_btn.clicked.connect(lambda: self.on_shape_selected("Cylinder"))
        self.semicircle_btn.clicked.connect(lambda: self.on_shape_selected("Semicircle"))
        
        # 툴바에 버튼 추가
        toolbar_layout.addWidget(self.rect_btn)
        toolbar_layout.addWidget(self.circle_btn)
        toolbar_layout.addWidget(self.cylinder_btn)
        toolbar_layout.addWidget(self.semicircle_btn)
        toolbar_layout.addWidget(self.map_size_btn)
        toolbar_layout.addStretch()  # 오른쪽 여백
        
        # 메인 레이아웃에 툴바 추가
        main_layout.addLayout(toolbar_layout)
        
        # 메인 에디터 영역 (맵 뷰 + 속성 패널)
        editor_layout = QHBoxLayout()
        
        # 맵 뷰 생성 및 설정
        self.map_view = self._create_map_view()
        
        # 속성 패널 생성
        properties_panel = QVBoxLayout()
        self.prop_layout = QFormLayout()
        
        # 속성 패널 그룹박스
        prop_group = QGroupBox("속성")
        prop_group.setLayout(self.prop_layout)
        
        # 속성 패널 초기화
        self.current_shape_type = "Rectangle"  # 기본값 설정
        
        # 속성 필드 초기화
        self._create_properties_panel()
        
        # 속성 패널에 그룹박스 추가
        properties_panel.addWidget(prop_group)
        properties_panel.addStretch()  # 하단 여백
        
        # 탭 위젯 생성 (맵 에디터 + 지형 에디터)
        self.tab_widget = QTabWidget()
        
        # 지형 편집 위젯 생성
        # 맵 에디터 탭
        map_tab = QWidget()
        map_tab_layout = QHBoxLayout()
        map_tab_layout.addWidget(self.map_view, 7)  # 70% 차지
        map_tab_layout.addLayout(properties_panel, 3)  # 30% 차지
        map_tab.setLayout(map_tab_layout)
        
        # 지형 에디터 탭
        terrain_tab = QWidget()
        terrain_tab_layout = QHBoxLayout()
        
        # 지형 미리보기 위젯
        self.preview_widget = PreviewWidget()
        self.preview_widget.terrain_clicked.connect(self.on_terrain_clicked)
        
        # 지형 편집 위젯
        self.terrain_editor = TerrainEditorWidget()
        self.terrain_editor.create_terrain_btn.clicked.connect(self.on_create_terrain)
        self.terrain_editor.add_platform_btn.clicked.connect(self.on_add_platform)
        self.terrain_editor.import_obj_btn.clicked.connect(self.on_import_obj)
        self.terrain_editor.export_unity_btn.clicked.connect(self.on_export_to_unity)
        
        # 탭 변경 이벤트 연결
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 지형 에디터 탭 레이아웃 설정
        terrain_tab_layout.addWidget(self.preview_widget, 7)  # 70% 차지
        terrain_tab_layout.addWidget(self.terrain_editor, 3)  # 30% 차지
        terrain_tab.setLayout(terrain_tab_layout)
        
        # 탭 추가
        self.tab_widget.addTab(map_tab, "맵 에디터")
        self.tab_widget.addTab(terrain_tab, "지형 에디터")
        
        # 메인 레이아웃에 탭 위젯 추가
        main_layout.addWidget(self.tab_widget)
        
        # 상태 바 설정 (필요한 경우)
        self.statusBar().showMessage("준비")
        
        # 메뉴바 설정 (필요한 경우)
        self._create_menubar()
        
        # 메인 위젯 설정
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 최초 속성 패널 업데이트
        self.update_properties_panel()
        
        # 도형 관련 변수 초기화 (여기서 초기화해도 됨)
        self.shapes = []  # 배치된 도형 목록
        self.is_placing = False  # 배치 모드 여부
        self.is_moving = False   # 이동 모드 여부
        self.current_shape = None  # 현재 생성 중인 도형
        self.selected_shape_index = None  # 선택된 도형 인덱스   

    def on_property_changed(self):
        """속성 값이 변경될 때 호출되는 메서드"""
        # 현재 선택된 도형의 속성 업데이트
        if self.current_shape_type == "Rectangle":
            # 사각형 속성 업데이트
            width = self.width_field.value()
            height = self.height_field.value()
            # 여기에 사각형 속성을 업데이트하는 코드 추가
            print(f"Rectangle updated: width={width}, height={height}")
            
        elif self.current_shape_type == "Circle":
            # 원 속성 업데이트
            radius = self.radius_field.value()
            # 여기에 원 속성을 업데이트하는 코드 추가
            print(f"Circle updated: radius={radius}")
            
        elif self.current_shape_type == "Semicircle":
            # 반원 속성 업데이트
            radius = self.semicircle_radius_field.value()
            # 여기에 반원 속성을 업데이트하는 코드 추가
            print(f"Semicircle updated: radius={radius}")
    
        # 화면 업데이트 (필요한 경우)
        self.update()  # 또는 특정 위젯/뷰 업데이트 메서드 호출

    def _create_shape_panel(self):
        # 도형 선택 그룹박스
        group_box = QGroupBox("도형 선택")
        layout = QVBoxLayout()
        
        # 버튼들
        self.rect_btn = QPushButton("사각형")
        self.circle_btn = QPushButton("원")
        self.cylinder_btn = QPushButton("실린더")
        self.semicircle_btn = QPushButton("반원")
        
        # 버튼 연결
        self.rect_btn.clicked.connect(lambda: self.on_shape_selected("Rectangle"))
        self.circle_btn.clicked.connect(lambda: self.on_shape_selected("Circle"))
        self.cylinder_btn.clicked.connect(lambda: self.on_shape_selected("Cylinder"))
        self.semicircle_btn.clicked.connect(lambda: self.on_shape_selected("Semicircle"))
        
        # 레이아웃에 추가
        layout.addWidget(self.rect_btn)
        layout.addWidget(self.circle_btn)
        layout.addWidget(self.cylinder_btn)
        layout.addWidget(self.semicircle_btn)
        
        group_box.setLayout(layout)
        
        # 수정: QVBoxLayout().addWidget() 대신 QVBoxLayout()을 생성하고 위젯 추가 후 레이아웃 반환
        result_layout = QVBoxLayout()
        result_layout.addWidget(group_box)
        return result_layout
        
    def _create_properties_panel(self):
        # 속성 입력 그룹박스
        self.prop_group = QGroupBox("속성")
        self.prop_layout = QFormLayout()
        
        # 기본 속성 필드
        self.width_field = QDoubleSpinBox()
        self.width_field.setRange(0.1, 100.0)
        self.width_field.setValue(10.0)
        self.width_field.setSuffix(" m")
        
        self.height_field = QDoubleSpinBox()
        self.height_field.setRange(0.1, 100.0)
        self.height_field.setValue(10.0)
        self.height_field.setSuffix(" m")
        
        self.depth_field = QDoubleSpinBox()
        self.depth_field.setRange(0.1, 10.0)
        self.depth_field.setValue(0.1)
        self.depth_field.setSuffix(" m")
        
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.1, 50.0)
        self.height_spinbox.setValue(1.0)
        self.height_spinbox.setSuffix(" m")
        self.height_spinbox.setSingleStep(0.5)
        self.height_spinbox.valueChanged.connect(self.on_property_changed)

        # 콜라이더 체크박스
        self.collider_check = QCheckBox("콜라이더 추가")
        self.collider_check.setChecked(True)
        
        # 속성 변경 연결
        self.width_field.valueChanged.connect(self.on_property_changed)
        self.height_field.valueChanged.connect(self.on_property_changed)
        self.depth_field.valueChanged.connect(self.on_property_changed)
        self.collider_check.stateChanged.connect(self.on_property_changed)

        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_selected_shape)
        button_layout.addWidget(self.delete_btn)
        
        # 레이아웃 초기 상태
        self.update_properties_panel()
        
        self.prop_group.setLayout(self.prop_layout)
        
        result_layout = QVBoxLayout()
        result_layout.addWidget(self.prop_group)
        
        # 도형 관리 버튼 그룹
        manage_group = QGroupBox("도형 관리")
        manage_layout = QVBoxLayout()
        manage_layout.addLayout(button_layout)
        manage_group.setLayout(manage_layout)
        result_layout.addWidget(manage_group)
        # 수정: QVBoxLayout().addWidget() 대신 QVBoxLayout()을 생성하고 위젯 추가 후 레이아웃 반환
        result_layout = QVBoxLayout()
        result_layout.addWidget(self.prop_group)
        return result_layout
        
    def _create_menubar(self):
        
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        new_action = QAction("새 프로젝트", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new_project)
        file_menu.addAction(new_action)
        
        # 불러오기 액션
        load_action = QAction("불러오기", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.on_load_project)
        file_menu.addAction(load_action)
        
        # 저장 액션
        save_action = QAction("저장", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.on_save_project)
        file_menu.addAction(save_action)

        edit_menu = menubar.addMenu("편집")
        # 삭제 액션
        delete_action = QAction("선택한 도형 삭제", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected_shape)
        edit_menu.addAction(delete_action)
        
        # 복제 액션
        duplicate_action = QAction("선택한 도형 복제", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.duplicate_selected_shape)
        edit_menu.addAction(duplicate_action)
        
        # 전체 선택 취소 액션
        clear_selection_action = QAction("선택 취소", self)
        clear_selection_action.setShortcut("Escape")
        clear_selection_action.triggered.connect(lambda: self.clear_selection())
        edit_menu.addAction(clear_selection_action)
        
        # 종료 액션
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 지형 메뉴 추가
        terrain_menu = menubar.addMenu("지형")
        
        # 지형 내보내기 액션
        export_terrain_action = QAction("Unity로 내보내기", self)
        export_terrain_action.triggered.connect(self.on_export_to_unity)
        terrain_menu.addAction(export_terrain_action)
        
        # 지형 초기화 액션
        reset_terrain_action = QAction("지형 초기화", self)
        reset_terrain_action.triggered.connect(self.on_reset_terrain)
        terrain_menu.addAction(reset_terrain_action)
        
    def update_properties_panel(self):
        # 현재 속성 패널 지우기
        while self.prop_layout.rowCount() > 0:
            self.prop_layout.removeRow(0)

        if self.current_shape is None:
            label = QLabel("도형을 선택하세요.")
            self.prop_layout.addRow(label)
            return

        # 새 필드들 생성 (매번 새로 생성)
        width_field = QDoubleSpinBox()
        width_field.setRange(0.1, 100.0)
        width_field.setValue(10.0)
        width_field.setSuffix(" m")
        
        height_field = QDoubleSpinBox()
        height_field.setRange(0.1, 100.0)
        height_field.setValue(10.0)
        height_field.setSuffix(" m")
        
        depth_field = QDoubleSpinBox()
        depth_field.setRange(0.1, 10.0)
        depth_field.setValue(0.1)
        depth_field.setSuffix(" m")

        collider_check = QCheckBox("콜라이더 추가")
        collider_check.setChecked(True)

        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.1, 50.0)
        self.height_spinbox.setValue(1.0)
        self.height_spinbox.setSuffix(" m")
        self.height_spinbox.setSingleStep(0.5)
        self.height_spinbox.valueChanged.connect(self.on_property_changed)
        
        # shape type에 따라 다르게 추가
        if self.current_shape == "Rectangle":
            self.prop_layout.addRow("너비:", width_field)
            self.prop_layout.addRow("높이:", height_field)
            self.prop_layout.addRow("두께:", depth_field)
            
        elif self.current_shape == "Circle":
            self.prop_layout.addRow("반지름:", width_field)
            self.prop_layout.addRow("두께:", depth_field)

        # ... 나머지도 동일하게 처리

        # 콜라이더 옵션 추가
        self.prop_layout.addRow("", collider_check)

        # 생성 버튼
        create_btn = QPushButton("생성")
        create_btn.clicked.connect(self.on_create_shape)
        self.prop_layout.addRow("", create_btn)

        # 필드 인스턴스 저장 (나중에 on_create_shape에서 참조하려면)
        self.width_field = width_field
        self.height_field = height_field
        self.depth_field = depth_field
        self.collider_check = collider_check

    def on_tab_changed(self, index):
        """탭 변경 시 처리"""
        if index == 1:  # 지형 탭
            # 지형 편집 모드 활성화
            self.preview_widget.set_brush(True, self.terrain_editor.get_brush_size())
            
            # 경사로 모드 확인
            if self.terrain_editor.get_tool_type() == 4:  # 경사로 도구
                self.preview_widget.set_ramp_mode(True)
            else:
                self.preview_widget.set_ramp_mode(False)
                
        else:
            # 지형 편집 모드 비활성화
            self.preview_widget.set_brush(False)
            self.preview_widget.set_ramp_mode(False)
    
    def on_create_shape(self):
        if self.current_shape is None:
            return
            
        # 도형 생성
        if self.current_shape == "Rectangle":
            shape = Rectangle(
                width=self.width_field.value(),
                height=self.height_field.value(),
                depth=self.depth_field.value()
            )
            
        elif self.current_shape == "Circle":
            shape = Circle(
                radius=self.width_field.value(),
                depth=self.depth_field.value()
            )
            
        elif self.current_shape == "Cylinder":
            # 실린더 구현...
            # 임시로 Circle과 같이 처리
            shape = Circle(
                radius=self.width_field.value(),
                depth=self.height_field.value()
            )
            
        elif self.current_shape == "Semicircle":
            # 반원 구현...
            # 임시로 Circle과 같이 처리하되 반지름만 절반으로
            shape = Circle(
                radius=self.width_field.value() / 2,
                depth=self.depth_field.value()
            )
            
        # 콜라이더 설정
        shape.has_collider = self.collider_check.isChecked()
        
        # 미리보기 업데이트
        self.preview_widget.set_mesh(shape.generate_mesh())
        self.preview_widget.update()
        
        # 현재 도형 저장
        self.current_created_shape = shape
        
    def on_create_terrain(self):
        """지형 생성 버튼 클릭 처리"""
        # 지형 생성 매개변수 가져오기
        params = self.terrain_editor.get_terrain_params()
        
        # 지형 객체 생성
        self.terrain = Terrain(
            width=params["width"],
            length=params["length"],
            resolution=params["resolution"],
            height_scale=params["height_scale"]
        )
        
        # 미리보기 업데이트
        self.preview_widget.set_terrain(self.terrain)
        self.preview_widget.set_brush(True, self.terrain_editor.get_brush_size())
        self.preview_widget.update()
        
        # 상태바 메시지 업데이트
        self.statusBar().showMessage(f"지형 생성 완료: {params['width']}m x {params['length']}m, 해상도: {params['resolution']} 격자/m")
    
    def on_terrain_clicked(self, x, z, button):
        """지형 클릭 이벤트 처리"""
        if self.terrain is None or self.tab_widget.currentIndex() != 1:
            return
            
        # 현재 도구 유형 가져오기
        tool_type = self.terrain_editor.get_tool_type()
        
        # 브러시 정보 가져오기
        brush_size = self.terrain_editor.get_brush_size()
        brush_strength = self.terrain_editor.get_brush_strength()
        
        # 도구 유형에 따라 처리
        # 높이기
        if tool_type == 0 and button == 1:  # 높이기 도구 + 왼쪽 버튼
            self.terrain.modify_height(x, z, brush_size, brush_strength, add=True)
            self.preview_widget.update()
            
        # 낮추기
        elif tool_type == 1 and button == 1:  # 낮추기 도구 + 왼쪽 버튼
            self.terrain.modify_height(x, z, brush_size, brush_strength, add=False)
            self.preview_widget.update()
            
        # 스무딩
        elif tool_type == 2 and button == 1:  # 스무딩 도구 + 왼쪽 버튼
            self.terrain.smooth_area(x, z, brush_size, brush_strength)
            self.preview_widget.update()
            
        # 평탄화
        elif tool_type == 3 and button == 1:  # 평탄화 도구 + 왼쪽 버튼
            self.terrain.flatten_area(x, z, brush_size)
            self.preview_widget.update()
        
        # 경사로 모드 처리
        if tool_type == 4:  # 경사로 도구
            if self.ramp_start_point is None:
                # 시작점 설정
                self.ramp_start_point = (x, 0, z)
                self.terrain_editor.set_ramp_mode(1)  # 끝점 선택 모드로
                self.preview_widget.ramp_start = self.ramp_start_point
                self.preview_widget.update()
                
                # 상태바 메시지 업데이트
                self.statusBar().showMessage("경사로 시작점 선택됨. 끝점을 선택하세요.")
            else:
                # 끝점 설정 및 경사로 생성
                ramp_params = self.terrain_editor.get_ramp_params()
                self.terrain.add_ramp(
                    self.ramp_start_point[0], self.ramp_start_point[2],
                    x, z,
                    ramp_params["width"],
                    ramp_params["start_height"],
                    ramp_params["end_height"]
                )
                
                # 상태 초기화
                self.ramp_start_point = None
                self.terrain_editor.set_ramp_mode(0)  # 시작점 선택 모드로
                self.preview_widget.ramp_start = None
                self.preview_widget.update()
                
                # 상태바 메시지 업데이트
                self.statusBar().showMessage("경사로 생성 완료")
                
    def on_add_platform(self):
        """플랫폼 추가 버튼 클릭 처리"""
        if self.terrain is None:
            QMessageBox.warning(self, "경고", "먼저 지형을 생성하세요.")
            return
            
        # 플랫폼 매개변수 가져오기
        params = self.terrain_editor.get_platform_params()
        
        # 플랫폼 위치 (지형 중앙)
        center_x = 0
        center_z = 0
        
        # 플랫폼 추가
        self.terrain.add_platform(
            center_x, center_z,
            params["width"], params["length"],
            params["height"]
        )
        
        # 미리보기 업데이트
        self.preview_widget.update()
        
        # 상태바 메시지 업데이트
        self.statusBar().showMessage(f"플랫폼 추가됨: {params['width']}m x {params['length']}m, 높이: {params['height']}m")

    def on_import_obj(self):
        # OBJ 파일 열기 대화상자
        filepath, _ = QFileDialog.getOpenFileName(
            self, "OBJ 파일 열기", "", "OBJ 파일 (*.obj)")
            
        if filepath:
            mesh = OBJLoader.load(filepath)
            if mesh:
                # 미리보기 업데이트
                self.preview_widget.set_mesh(mesh)
                self.preview_widget.update()
                
                # 상태바 메시지 업데이트
                self.statusBar().showMessage(f"OBJ 파일 로드됨: {filepath}")
            else:
                QMessageBox.critical(self, "오류", "OBJ 파일을 로드할 수 없습니다.")


    def on_export_to_unity(self):
        """유니티로 내보내기 버튼 클릭 시 처리"""
        if self.terrain is None:
            QMessageBox.warning(self, "경고", "먼저 지형을 생성하세요.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "유니티 파일로 저장", "", "JSON 파일 (*.json)")
        
        if filepath:
            try:
                # 디버깅 코드 추가
                print(f"Exporting terrain to: {filepath}")
                print(f"Terrain object: {self.terrain}")
                print(f"export_heightmap method: {getattr(self.terrain, 'export_heightmap', None)}")
                
                # UnityExporter.export 호출
                UnityExporter.export(self.terrain, filepath)
                QMessageBox.information(self, "성공", "유니티 파일로 성공적으로 내보냈습니다.")
                
                # 상태바 메시지 업데이트
                self.statusBar().showMessage(f"지형이 유니티 파일로 내보내졌습니다: {filepath}")
            except Exception as e:
                # 자세한 오류 정보 표시
                import traceback
                error_msg = f"내보내기 실패:\n{str(e)}\n\n{traceback.format_exc()}"
                print(error_msg)
                QMessageBox.critical(self, "오류", error_msg)

    
    def on_reset_terrain(self):
            """지형 초기화"""
            if self.terrain is None:
                return
                
            reply = QMessageBox.question(
                self, "지형 초기화", 
                "현재 지형을 초기화하시겠습니까? 모든 지형 데이터가 삭제됩니다.",
                QMessageBox.Yes | QMessageBox.No)
                
            if reply == QMessageBox.Yes:
                # 지형 초기화
                params = self.terrain_editor.get_terrain_params()
                self.terrain = Terrain(
                    width=params["width"],
                    length=params["length"],
                    resolution=params["resolution"],
                    height_scale=params["height_scale"]
                )
                
                # 미리보기 업데이트
                self.preview_widget.set_terrain(self.terrain)
                self.preview_widget.update()
                
                # 경사로 시작점 초기화
                self.ramp_start_point = None
                self.preview_widget.ramp_start = None
                
                # 상태바 메시지 업데이트
                self.statusBar().showMessage("지형이 초기화되었습니다.")

    def _create_map_view(self):
        """맵 편집 영역 생성"""
        map_view = QWidget()
        map_view.setMinimumSize(self.map_width, self.map_height)
        map_view.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CCCCCC;")
        
        # 마우스 이벤트 처리 설정
        map_view.setMouseTracking(True)
        map_view.mousePressEvent = self.map_view_mouse_press
        map_view.mouseReleaseEvent = self.map_view_mouse_release
        map_view.mouseMoveEvent = self.map_view_mouse_move
        map_view.paintEvent = self.map_view_paint
        
        return map_view  # 여기서는 객체를 반환만 하고 self.map_view에 저장하지 않음
    
    def map_view_mouse_press(self, event):
        """맵 뷰에서 마우스 누를 때 처리"""
        if event.button() == Qt.LeftButton:
            # 도형 선택 또는 이동 모드 설정
            pos = event.pos()
            
            # 기존 도형을 클릭했는지 확인
            for i, shape in enumerate(self.shapes):
                if self.is_point_in_shape(pos, shape):
                    self.selected_shape_index = i
                    self.is_moving = True
                    self.move_start_point = pos
                    self.shape_start_pos = {'x': shape['x'], 'y': shape['y']}
                    self.map_view.update()
                    return
            
            # 새 도형 생성 모드
            self.is_placing = True
            self.start_point = pos
            
            # 도형 유형에 따라 임시 도형 생성
            self.current_shape = {
                'type': self.current_shape_type,
                'x': pos.x(),
                'y': pos.y(),
                'properties': self.get_current_properties()
            }
            
            # 기본 크기 설정
            if self.current_shape_type == "Rectangle":
                self.current_shape['width'] = 0
                self.current_shape['height'] = 0
            elif self.current_shape_type in ["Circle", "Cylinder", "Semicircle"]:
                self.current_shape['radius'] = 0
            
            # 맵 뷰 업데이트
            self.map_view.update()
        elif event.button() == Qt.RightButton:
        # 우클릭 메뉴 표시
            pos = event.pos()
            
            # 도형 위에서 우클릭한 경우
            for i, shape in enumerate(self.shapes):
                if self.is_point_in_shape(pos, shape):
                    self.selected_shape_index = i
                    self.map_view.update()
                    
                    # 콘텍스트 메뉴 생성
                    context_menu = QMenu(self)
                    
                    # 삭제 액션
                    delete_action = QAction("삭제", self)
                    delete_action.triggered.connect(self.delete_selected_shape)
                    context_menu.addAction(delete_action)
                    
                    # 도형 복제 액션
                    duplicate_action = QAction("복제", self)
                    duplicate_action.triggered.connect(self.duplicate_selected_shape)
                    context_menu.addAction(duplicate_action)
                    
                    # 메뉴 표시
                    context_menu.exec_(event.globalPos())
                    return
            
    def map_view_mouse_release(self, event):
        """맵 뷰에서 마우스 뗄 때 처리"""
        if event.button() == Qt.LeftButton:
            if self.is_moving:
                self.is_moving = False
                # 이동 완료
            elif self.is_placing and self.current_shape:
                self.is_placing = False
                
                # 최소 크기 확인 - 너무 작으면 생성하지 않음
                if self.current_shape_type == "Rectangle":
                    if self.current_shape['width'] < 5 or self.current_shape['height'] < 5:
                        self.current_shape = None
                        self.map_view.update()
                        return
                elif self.current_shape_type in ["Circle", "Cylinder", "Semicircle"]:
                    if self.current_shape['radius'] < 5:
                        self.current_shape = None
                        self.map_view.update()
                        return
                
                # 완성된 도형을 목록에 추가
                self.shapes.append(self.current_shape)
                self.selected_shape_index = len(self.shapes) - 1
                self.current_shape = None
                
                # 맵 뷰 업데이트
                self.map_view.update()
                print(f"도형 배치 완료: {self.shapes[-1]}")

    def map_view_mouse_move(self, event):
        """맵 뷰에서 마우스 이동 시 처리"""
        current_pos = event.pos()
        
        if self.is_moving and hasattr(self, 'selected_shape_index') and self.selected_shape_index is not None:
            # 선택된 도형 이동
            dx = current_pos.x() - self.move_start_point.x()
            dy = current_pos.y() - self.move_start_point.y()
            
            shape = self.shapes[self.selected_shape_index]
            shape['x'] = self.shape_start_pos['x'] + dx
            shape['y'] = self.shape_start_pos['y'] + dy
            
            self.map_view.update()
        elif self.is_placing and self.current_shape:
            # 현재 마우스 위치에 따라 도형 크기 업데이트
            if self.current_shape_type == "Rectangle":
                self.current_shape['width'] = abs(current_pos.x() - self.start_point.x())
                self.current_shape['height'] = abs(current_pos.y() - self.start_point.y())
                self.current_shape['x'] = min(self.start_point.x(), current_pos.x())
                self.current_shape['y'] = min(self.start_point.y(), current_pos.y())
            elif self.current_shape_type in ["Circle", "Cylinder", "Semicircle"]:
                dx = current_pos.x() - self.start_point.x()
                dy = current_pos.y() - self.start_point.y()
                self.current_shape['radius'] = (dx**2 + dy**2)**0.5
            
            self.map_view.update()
            
    def map_view_paint(self, event):
        """맵 뷰 그리기 이벤트"""
        painter = QPainter(self.map_view)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 격자 그리기 (선택 사항)
        self.draw_grid(painter)
        
        # 기존 도형 그리기
        for i, shape in enumerate(self.shapes):
            # 선택된 도형은 하이라이트
            is_selected = hasattr(self, 'selected_shape_index') and i == self.selected_shape_index
            self.draw_shape(painter, shape, is_selected=is_selected)
        
        # 현재 배치 중인 도형 그리기 (있는 경우)
        if self.current_shape and self.is_placing:
            self.draw_shape(painter, self.current_shape, is_preview=True)
        
        painter.end()

    def draw_grid(self, painter, grid_size=50):
        """격자 그리기"""
        # view_size = self.sender().size()
        view_size = self.map_view.size()
        width, height = view_size.width(), view_size.height()
        
        painter.setPen(QPen(QColor("#EEEEEE"), 1))
        
        # 수직선
        for x in range(0, width, grid_size):
            painter.drawLine(x, 0, x, height)
        
        # 수평선
        for y in range(0, height, grid_size):
            painter.drawLine(0, y, width, y)

    def draw_shape(self, painter, shape, is_preview=False, is_selected=False):
        """도형 그리기"""
        # 스타일 설정
        if is_preview:
            painter.setPen(QPen(QColor("#3498db"), 2, Qt.DashLine))
            painter.setBrush(QColor(52, 152, 219, 100))  # 반투명 파란색
        elif is_selected:
            painter.setPen(QPen(QColor("#e74c3c"), 2))  # 빨간색 테두리
            painter.setBrush(QColor(231, 76, 60, 150))   # 선택된 도형은 빨간색
        else:
            painter.setPen(QPen(QColor("#2c3e50"), 2))
            painter.setBrush(QColor(52, 152, 219, 180))  # 진한 파란색
        
        # 도형 유형에 따라 그리기
        if shape['type'] == "Rectangle":
            painter.drawRect(int(shape['x']), int(shape['y']), int(shape['width']), int(shape['height']))
            
            # 객체 높이 표시 (있는 경우)
            if 'object_height' in shape and shape['object_height'] > 0:
                # 높이 표시 - 도형 내부에 높이 값 텍스트 추가
                height_text = f"H: {shape['object_height']} m"
                painter.drawText(int(shape['x'] + 5), int(shape['y'] + 20), height_text)
        
        elif shape['type'] in ["Circle", "Cylinder"]:
            radius = shape['radius']
            painter.drawEllipse(int(shape['x'] - radius), int(shape['y'] - radius), 
                            int(radius * 2), int(radius * 2))
                            
            # 객체 높이 표시 (있는 경우)
            if 'object_height' in shape and shape['object_height'] > 0:
                height_text = f"H: {shape['object_height']} m"
                painter.drawText(int(shape['x'] - 20), int(shape['y']), height_text)
        
        elif shape['type'] == "Semicircle":
            radius = shape['radius']
            # 반원 그리기
            painter.drawChord(int(shape['x'] - radius), int(shape['y'] - radius),
                            int(radius * 2), int(radius * 2), 0 * 16, 180 * 16)
                            
            # 객체 높이 표시 (있는 경우)
            if 'object_height' in shape and shape['object_height'] > 0:
                height_text = f"H: {shape['object_height']} m"
                painter.drawText(int(shape['x'] - 20), int(shape['y'] - radius - 10), height_text)

    def get_current_properties(self):
        """현재 설정된 속성 가져오기"""
        props = {}
        
        if self.current_shape_type == "Rectangle":
            if hasattr(self, 'width_field'):
                props['width'] = self.width_field.value()
            else:
                props['width'] = 100  # 기본값
                
            if hasattr(self, 'height_field'):
                props['height'] = self.height_field.value()
            else:
                props['height'] = 100  # 기본값
                
        elif self.current_shape_type == "Circle":
            if hasattr(self, 'radius_field'):
                props['radius'] = self.radius_field.value()
            else:
                props['radius'] = 50  # 기본값
                
        elif self.current_shape_type == "Semicircle":
            if hasattr(self, 'semicircle_radius_field'):
                props['radius'] = self.semicircle_radius_field.value()
            else:
                props['radius'] = 50  # 기본값
        
        return props

    def update_shape_list(self):
        """도형 목록 위젯 업데이트 (구현이 필요하다면)"""
        # 도형 목록을 표시하는 위젯이 있다면 여기서 업데이트
        pass

    def on_shape_selected(self, shape_type):
        """도형 유형 선택 시 호출"""
        self.current_shape_type = shape_type
        print(f"도형 선택: {shape_type}")
        
        self.update_properties_panel()
        
        if not hasattr(self, 'map_view') or self.map_view is None:
            print("맵 뷰가 아직 초기화되지 않았습니다.")
            return
        
        center_x = self.map_view.width() // 2
        center_y = self.map_view.height() // 2
        
        object_height = 1.0
        if hasattr(self, 'height_spinbox'):
            object_height = self.height_spinbox.value()


        # 도형 생성
        if shape_type == "Rectangle":
            width = 100 if not hasattr(self, 'width_field') else self.width_field.value()
            height = 100 if not hasattr(self, 'height_field') else self.height_field.value()
            new_shape = {
                'type': shape_type,
                'x': center_x - width // 2,
                'y': center_y - height // 2,
                'width': width,
                'height': height,
                'object_height': object_height,
                'properties': self.get_current_properties()
            }
        elif shape_type in ["Circle", "Cylinder"]:
            radius = 50 if not hasattr(self, 'radius_field') else self.radius_field.value()
            new_shape = {
                'type': shape_type,
                'x': center_x,
                'y': center_y,
                'radius': radius,
                'object_height': object_height,
                'properties': self.get_current_properties()
            }
        elif shape_type == "Semicircle":
            radius = 50 if not hasattr(self, 'semicircle_radius_field') else self.semicircle_radius_field.value()
            new_shape = {
                'type': shape_type,
                'x': center_x,
                'y': center_y,
                'radius': radius,
                'object_height': object_height,
                'properties': self.get_current_properties()
            }
        else:
            return

        # ✅ 기존 도형 유지 + 새 도형 추가
        if not hasattr(self, 'shapes'):
            self.shapes = []

        self.shapes.append(new_shape)  # ← 여기 핵심!

        self.selected_shape_index = len(self.shapes) - 1
        self.map_view.update()

    def is_point_in_shape(self, point, shape):
        """주어진 점이 도형 내부에 있는지 확인"""
        if shape['type'] == "Rectangle":
            return (shape['x'] <= point.x() <= shape['x'] + shape['width'] and
                    shape['y'] <= point.y() <= shape['y'] + shape['height'])
        elif shape['type'] in ["Circle", "Cylinder"]:
            dx = point.x() - shape['x']
            dy = point.y() - shape['y']
            return (dx**2 + dy**2) <= shape['radius']**2
        elif shape['type'] == "Semicircle":
            dx = point.x() - shape['x']
            dy = point.y() - shape['y']
            distance = (dx**2 + dy**2)**0.5
            # 반경 내에 있고 y좌표가 중심점보다 작거나 같은 경우
            return distance <= shape['radius'] and point.y() <= shape['y']
        
        return False

    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        # Delete 키 처리
        if event.key() == Qt.Key_Delete:
            self.delete_selected_shape()
        # 키보드 단축키 추가 (필요하다면)
        elif event.key() == Qt.Key_Escape:
            # ESC 키: 선택 취소
            self.selected_shape_index = None
            if hasattr(self, 'map_view') and self.map_view is not None:
                self.map_view.update()
        
        super().keyPressEvent(event)

    def delete_selected_shape(self):
        """선택된 도형 삭제"""
        if hasattr(self, 'selected_shape_index') and self.selected_shape_index is not None:
            if 0 <= self.selected_shape_index < len(self.shapes):
                # 도형 삭제
                del self.shapes[self.selected_shape_index]
                print(f"도형 삭제됨. 남은 도형 수: {len(self.shapes)}")
                
                # 선택 초기화
                self.selected_shape_index = None
                
                # 맵 뷰 업데이트
                if hasattr(self, 'map_view') and self.map_view is not None:
                    self.map_view.update()

    # 5. 도형 복제 기능 추가
    def duplicate_selected_shape(self):
        """선택된 도형 복제"""
        if hasattr(self, 'selected_shape_index') and self.selected_shape_index is not None:
            if 0 <= self.selected_shape_index < len(self.shapes):
                # 원본 도형
                original = self.shapes[self.selected_shape_index]
                
                # 도형 복제 (깊은 복사)
                import copy
                new_shape = copy.deepcopy(original)
                
                # 약간 오프셋을 주어 겹치지 않게 함
                new_shape['x'] += 20
                new_shape['y'] += 20
                
                # 복제된 도형 추가
                self.shapes.append(new_shape)
                
                # 새 도형 선택
                self.selected_shape_index = len(self.shapes) - 1
                
                print(f"도형 복제됨. 현재 도형 수: {len(self.shapes)}")
                
                # 맵 뷰 업데이트
                if hasattr(self, 'map_view') and self.map_view is not None:
                    self.map_view.update()

    def clear_selection(self):
        """도형 선택 취소"""
        self.selected_shape_index = None
        if hasattr(self, 'map_view') and self.map_view is not None:
            self.map_view.update()


    def show_map_size_dialog(self):
        """맵 크기 조정 대화상자 표시"""
        dialog = QWidget()
        dialog.setWindowTitle("맵 크기 조정")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # 너비 설정
        width_layout = QHBoxLayout()
        width_label = QLabel("맵 너비:")
        width_spinbox = QDoubleSpinBox()
        width_spinbox.setRange(100, 3000)
        width_spinbox.setValue(self.map_width)
        width_spinbox.setSuffix(" px")
        width_layout.addWidget(width_label)
        width_layout.addWidget(width_spinbox)
        
        # 높이 설정
        height_layout = QHBoxLayout()
        height_label = QLabel("맵 높이:")
        height_spinbox = QDoubleSpinBox()
        height_spinbox.setRange(100, 3000)
        height_spinbox.setValue(self.map_height)
        height_spinbox.setSuffix(" px")
        height_layout.addWidget(height_label)
        height_layout.addWidget(height_spinbox)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        ok_button = QPushButton("확인")
        cancel_button = QPushButton("취소")
        
        ok_button.clicked.connect(lambda: self.resize_map(int(width_spinbox.value()), int(height_spinbox.value()), dialog))
        cancel_button.clicked.connect(dialog.close)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        # 레이아웃 설정
        layout.addLayout(width_layout)
        layout.addLayout(height_layout)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.show()

    def resize_map(self, width, height, dialog):
        """맵 크기 조정"""
        self.map_width = width
        self.map_height = height
        
        # 맵 뷰 크기 업데이트
        self.map_view.setMinimumSize(width, height)
        
        # 대화상자 닫기
        dialog.close()
        
        # 맵 업데이트
        self.map_view.update()
        
        # 상태 메시지 업데이트
        self.statusBar().showMessage(f"맵 크기가 변경되었습니다: {width} x {height}")

    def on_save_project(self):
        """프로젝트 저장 메서드"""
        # 저장할 파일 경로 선택 대화상자
        filepath, _ = QFileDialog.getSaveFileName(
            self, "프로젝트 저장", "", "맵 에디터 파일 (*.json)")
            
        if not filepath:
            return  # 취소 시 종료
            
        # .json 확장자 확인 및 추가
        if not filepath.endswith('.json'):
            filepath += '.json'
        
        # 현재 맵 데이터 수집
        map_data = {
            'version': '3.0',  # 버전 업데이트
            'map_width': self.map_width,
            'map_height': self.map_height,
            'shapes': self.shapes,
        }
        
        # 지형 데이터가 있으면 추가
        if self.terrain is not None:
            terrain_data = self.terrain.get_heightmap_data()  # ✅ 이제 JSON 저장용 dict 반환됨
            map_data['terrain'] = terrain_data
        
        try:
            # JSON으로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=2)
            
            # 성공 메시지
            self.statusBar().showMessage(f"프로젝트가 성공적으로 저장되었습니다: {filepath}")
            QMessageBox.information(self, "저장 완료", f"프로젝트가 성공적으로 저장되었습니다.\n{filepath}")
        except Exception as e:
            # 오류 메시지
            QMessageBox.critical(self, "저장 오류", f"프로젝트 저장 중 오류가 발생했습니다.\n{str(e)}")
            print(f"저장 오류: {str(e)}")

    def on_load_project(self):
        """프로젝트 불러오기 메서드"""
        # 파일 선택 대화상자
        filepath, _ = QFileDialog.getOpenFileName(
            self, "프로젝트 불러오기", "", "맵 에디터 파일 (*.json)")
            
        if not filepath:
            return  # 취소 시 종료
        
        try:
            # JSON 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            # 버전 확인 (향후 버전 호환성을 위해)
            version = map_data.get('version', '1.0')
            
            # 맵 크기 업데이트
            if 'map_width' in map_data and 'map_height' in map_data:
                self.map_width = map_data['map_width']
                self.map_height = map_data['map_height']
                self.map_view.setMinimumSize(self.map_width, self.map_height)
            
            # 도형 데이터 로드
            if 'shapes' in map_data:
                self.shapes = map_data['shapes']
            else:
                self.shapes = []
            
            # 지형 데이터 로드 (버전 3.0 이상)
            if 'terrain' in map_data and version >= '3.0':
                terrain_data = map_data['terrain']
                
                # 지형 객체 생성
                self.terrain = Terrain(
                    width=terrain_data['width'],
                    length=terrain_data['length'],
                    resolution=terrain_data['resolution'],
                    height_scale=terrain_data['height_scale']
                )
                
                # 높이맵 설정
                import numpy as np
                self.terrain.heightmap = np.array(terrain_data['heightmap'])
                
                # 지형 오브젝트 설정
                self.terrain.terrain_objects = terrain_data['terrain_objects']
                
                # 지형 미리보기 업데이트
                self.preview_widget.set_terrain(self.terrain)
                self.preview_widget.update()
            
            # 선택 초기화
            self.selected_shape_index = None
            
            # 맵 뷰 업데이트
            self.map_view.update()
            
            # 성공 메시지
            self.statusBar().showMessage(f"프로젝트를 성공적으로 불러왔습니다: {filepath}")
            QMessageBox.information(self, "불러오기 완료", f"프로젝트를 성공적으로 불러왔습니다.\n{filepath}")
        except Exception as e:
            # 오류 메시지
            QMessageBox.critical(self, "불러오기 오류", f"프로젝트 불러오기 중 오류가 발생했습니다.\n{str(e)}")
            print(f"불러오기 오류: {str(e)}")

    def on_new_project(self):
        """새 프로젝트 생성"""
        # 현재 작업 내용이 있는 경우 저장 확인
        if self.shapes or self.terrain is not None:
            reply = QMessageBox.question(
                self, "새 프로젝트", 
                "현재 작업 내용을 저장하시겠습니까?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                self.on_save_project()
            elif reply == QMessageBox.Cancel:
                return  # 취소 시 종료
        
        # 새 프로젝트 초기화
        self.shapes = []
        self.selected_shape_index = None
        
        # 지형 초기화
        self.terrain = None
        self.ramp_start_point = None
        self.preview_widget.set_terrain(None)
        self.preview_widget.update()
        
        # 맵 크기 초기화 (기본값으로)
        self.map_width = 800
        self.map_height = 600
        self.map_view.setMinimumSize(self.map_width, self.map_height)
        
        # 맵