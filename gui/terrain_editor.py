# gui/terrain_editor.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QLabel, QDoubleSpinBox, QComboBox, QPushButton,
                            QSlider, QTabWidget, QFormLayout, QFileDialog,
                            QMessageBox)
from PyQt5.QtCore import Qt

class TerrainEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 현재 선택된 도구 (0: 높이기, 1: 낮추기, 2: 스무딩, 3: 평탄화, 4: 경사로)
        self.current_tool = 0
        
        # 경사로 모드 (0: 시작점 선택, 1: 끝점 선택)
        self.ramp_mode = 0
        
        # UI 초기화
        self._init_ui()
    
    def _init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 지형 생성 그룹박스
        creation_group = QGroupBox("지형 생성")
        creation_layout = QFormLayout()
        
        # 지형 크기 설정
        self.width_field = QDoubleSpinBox()
        self.width_field.setRange(10.0, 1000.0)
        self.width_field.setValue(100.0)
        self.width_field.setSuffix(" m")
        self.width_field.setSingleStep(10.0)
        
        self.length_field = QDoubleSpinBox()
        self.length_field.setRange(10.0, 1000.0)
        self.length_field.setValue(100.0)
        self.length_field.setSuffix(" m")
        self.length_field.setSingleStep(10.0)
        
        # 해상도 설정
        self.resolution_field = QDoubleSpinBox()
        self.resolution_field.setRange(0.1, 5.0)
        self.resolution_field.setValue(1.0)
        self.resolution_field.setSuffix(" 격자/m")
        self.resolution_field.setSingleStep(0.1)
        
        # 높이 스케일 설정
        self.height_scale_field = QDoubleSpinBox()
        self.height_scale_field.setRange(1.0, 100.0)
        self.height_scale_field.setValue(10.0)
        self.height_scale_field.setSuffix(" m")
        self.height_scale_field.setSingleStep(1.0)
        
        # 지형 생성 버튼
        self.create_terrain_btn = QPushButton("지형 생성")
        
        # 폼 레이아웃에 위젯 추가
        creation_layout.addRow("너비:", self.width_field)
        creation_layout.addRow("길이:", self.length_field)
        creation_layout.addRow("해상도:", self.resolution_field)
        creation_layout.addRow("최대 높이:", self.height_scale_field)
        creation_layout.addRow("", self.create_terrain_btn)
        
        creation_group.setLayout(creation_layout)
        
        # 지형 편집 도구 탭 위젯
        tools_tabs = QTabWidget()
        
        # 브러시 도구 탭
        brush_tab = QWidget()
        brush_layout = QVBoxLayout()
        
        # 도구 선택 콤보박스
        tool_layout = QFormLayout()
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["높이기", "낮추기", "스무딩", "평탄화", "경사로"])
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)
        
        tool_layout.addRow("도구:", self.tool_combo)
        brush_layout.addLayout(tool_layout)
        
        # 브러시 설정 그룹
        brush_group = QGroupBox("브러시 설정")
        brush_settings_layout = QFormLayout()
        
        # 브러시 크기 슬라이더
        self.brush_size_slider = QSlider(Qt.Horizontal)
        self.brush_size_slider.setRange(1, 20)
        self.brush_size_slider.setValue(5)
        self.brush_size_slider.setTickPosition(QSlider.TicksBelow)
        self.brush_size_label = QLabel("5.0 m")
        
        # 슬라이더 값 변경 시 레이블 업데이트
        self.brush_size_slider.valueChanged.connect(self.update_brush_size_label)
        
        # 브러시 강도 슬라이더
        self.brush_strength_slider = QSlider(Qt.Horizontal)
        self.brush_strength_slider.setRange(1, 10)
        self.brush_strength_slider.setValue(5)
        self.brush_strength_slider.setTickPosition(QSlider.TicksBelow)
        self.brush_strength_label = QLabel("50%")
        
        # 슬라이더 값 변경 시 레이블 업데이트
        self.brush_strength_slider.valueChanged.connect(self.update_brush_strength_label)
        
        # 브러시 설정 추가
        brush_settings_layout.addRow("크기:", self.brush_size_slider)
        brush_settings_layout.addRow("", self.brush_size_label)
        brush_settings_layout.addRow("강도:", self.brush_strength_slider)
        brush_settings_layout.addRow("", self.brush_strength_label)
        
        brush_group.setLayout(brush_settings_layout)
        brush_layout.addWidget(brush_group)
        
        # 경사로 설정 그룹
        ramp_group = QGroupBox("경사로 설정")
        ramp_layout = QFormLayout()
        
        # 경사로 너비 설정
        self.ramp_width_field = QDoubleSpinBox()
        self.ramp_width_field.setRange(1.0, 50.0)
        self.ramp_width_field.setValue(5.0)
        self.ramp_width_field.setSuffix(" m")
        
        # 경사로 시작/끝 높이 설정
        self.ramp_start_height_field = QDoubleSpinBox()
        self.ramp_start_height_field.setRange(0.0, 50.0)
        self.ramp_start_height_field.setValue(0.0)
        self.ramp_start_height_field.setSuffix(" m")
        
        self.ramp_end_height_field = QDoubleSpinBox()
        self.ramp_end_height_field.setRange(0.0, 50.0)
        self.ramp_end_height_field.setValue(5.0)
        self.ramp_end_height_field.setSuffix(" m")
        
        # 경사로 상태 레이블
        self.ramp_status_label = QLabel("시작점을 선택하세요")
        
        # 경사로 설정 추가
        ramp_layout.addRow("너비:", self.ramp_width_field)
        ramp_layout.addRow("시작 높이:", self.ramp_start_height_field)
        ramp_layout.addRow("끝 높이:", self.ramp_end_height_field)
        ramp_layout.addRow("상태:", self.ramp_status_label)
        
        ramp_group.setLayout(ramp_layout)
        brush_layout.addWidget(ramp_group)
        
        # 브러시 탭 최종 설정
        brush_tab.setLayout(brush_layout)
        
        # 플랫폼 추가 탭
        platform_tab = QWidget()
        platform_layout = QVBoxLayout()
        
        # 플랫폼 설정 그룹
        platform_group = QGroupBox("플랫폼 설정")
        platform_settings_layout = QFormLayout()
        
        # 플랫폼 크기 설정
        self.platform_width_field = QDoubleSpinBox()
        self.platform_width_field.setRange(1.0, 50.0)
        self.platform_width_field.setValue(10.0)
        self.platform_width_field.setSuffix(" m")
        
        self.platform_length_field = QDoubleSpinBox()
        self.platform_length_field.setRange(1.0, 50.0)
        self.platform_length_field.setValue(10.0)
        self.platform_length_field.setSuffix(" m")
        
        # 플랫폼 높이 설정
        self.platform_height_field = QDoubleSpinBox()
        self.platform_height_field.setRange(0.1, 50.0)
        self.platform_height_field.setValue(5.0)
        self.platform_height_field.setSuffix(" m")
        
        # 플랫폼 추가 버튼
        self.add_platform_btn = QPushButton("플랫폼 추가")
        
        # 플랫폼 설정 추가
        platform_settings_layout.addRow("너비 (X):", self.platform_width_field)
        platform_settings_layout.addRow("길이 (Z):", self.platform_length_field)
        platform_settings_layout.addRow("높이:", self.platform_height_field)
        platform_settings_layout.addRow("", self.add_platform_btn)
        
        platform_group.setLayout(platform_settings_layout)
        platform_layout.addWidget(platform_group)
        
        # 플랫폼 탭 최종 설정
        platform_tab.setLayout(platform_layout)
        
        # 임포트/익스포트 탭
        export_tab = QWidget()
        export_layout = QVBoxLayout()
        
        # OBJ 임포트 그룹
        import_group = QGroupBox("OBJ 파일 임포트")
        import_layout = QHBoxLayout()
        
        # OBJ 임포트 버튼
        self.import_obj_btn = QPushButton("OBJ 파일 열기")
        import_layout.addWidget(self.import_obj_btn)
        
        import_group.setLayout(import_layout)
        export_layout.addWidget(import_group)
        
        # 유니티 익스포트 그룹
        unity_group = QGroupBox("유니티로 내보내기")
        unity_layout = QHBoxLayout()
        
        # 유니티 익스포트 버튼
        self.export_unity_btn = QPushButton("유니티 파일로 저장")
        unity_layout.addWidget(self.export_unity_btn)
        
        unity_group.setLayout(unity_layout)
        export_layout.addWidget(unity_group)
        
        # 익스포트 탭 최종 설정
        export_tab.setLayout(export_layout)
        
        # 탭 추가
        tools_tabs.addTab(brush_tab, "브러시 도구")
        tools_tabs.addTab(platform_tab, "플랫폼 추가")
        tools_tabs.addTab(export_tab, "임포트/익스포트")
        
        # 메인 레이아웃에 위젯 추가
        main_layout.addWidget(creation_group)
        main_layout.addWidget(tools_tabs)
        
        # 레이아웃 설정
        self.setLayout(main_layout)
    
    def update_brush_size_label(self):
        """브러시 크기 레이블 업데이트"""
        size = self.brush_size_slider.value()
        self.brush_size_label.setText(f"{size}.0 m")
    
    def update_brush_strength_label(self):
        """브러시 강도 레이블 업데이트"""
        strength = self.brush_strength_slider.value() * 10
        self.brush_strength_label.setText(f"{strength}%")
    
    def on_tool_changed(self, index):
        """도구 변경 시 처리"""
        self.current_tool = index
        
        # 경사로 모드 업데이트
        if index == 4:  # 경사로 도구
            self.ramp_status_label.setText("시작점을 선택하세요")
            self.ramp_mode = 0
        else:
            self.ramp_mode = -1  # 경사로 모드 비활성화
    
    def set_ramp_mode(self, mode):
        """경사로 모드 설정"""
        self.ramp_mode = mode
        
        if mode == 0:
            self.ramp_status_label.setText("시작점을 선택하세요")
        else:
            self.ramp_status_label.setText("끝점을 선택하세요")
    
    def get_tool_type(self):
        """현재 선택된 도구 유형 반환"""
        return self.current_tool
    
    def get_brush_size(self):
        """브러시 크기 반환"""
        return self.brush_size_slider.value()
    
    def get_brush_strength(self):
        """브러시 강도 반환 (0.0 ~ 1.0)"""
        return self.brush_strength_slider.value() / 10.0
    
    def get_terrain_params(self):
        """지형 생성 매개변수 반환"""
        return {
            "width": self.width_field.value(),
            "length": self.length_field.value(),
            "resolution": self.resolution_field.value(),
            "height_scale": self.height_scale_field.value()
        }
    
    def get_ramp_params(self):
        """경사로 매개변수 반환"""
        return {
            "width": self.ramp_width_field.value(),
            "start_height": self.ramp_start_height_field.value(),
            "end_height": self.ramp_end_height_field.value()
        }
    
    def get_platform_params(self):
        """플랫폼 매개변수 반환"""
        return {
            "width": self.platform_width_field.value(),
            "length": self.platform_length_field.value(),
            "height": self.platform_height_field.value()
        }