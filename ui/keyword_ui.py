"""
关键词管理UI - 管理关键词回复规则
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QSpinBox, QCheckBox, QHeaderView, QMessageBox, QDialog,
                             QTextEdit, QLabel, QGroupBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, List
from tts.keyword_matcher import KeywordRule
from config.log import g_logger


class KeywordRuleDialog(QDialog):
    """关键词规则编辑对话框"""
    
    def __init__(self, keyword: str = None, rule: KeywordRule = None, parent=None):
        super().__init__(parent)
        self.keyword = keyword or ""
        self.rule = rule or KeywordRule(keyword=self.keyword)
        self.setWindowTitle("编辑关键词规则")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 关键词输入
        form_layout = QFormLayout()
        
        self.keyword_input = QLineEdit(self.keyword)
        self.keyword_input.setPlaceholderText("输入关键词")
        form_layout.addRow("关键词:", self.keyword_input)
        
        # 匹配方式
        self.match_type_combo = QComboBox()
        self.match_type_combo.addItems(["contain", "exact", "regex"])
        self.match_type_combo.setCurrentText(self.rule.match_type)
        form_layout.addRow("匹配方式:", self.match_type_combo)
        
        # 优先级
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 10)
        self.priority_spin.setValue(self.rule.priority)
        form_layout.addRow("优先级:", self.priority_spin)
        
        # 冷却时间
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 300)
        self.cooldown_spin.setValue(self.rule.cooldown)
        self.cooldown_spin.setSuffix(" 秒")
        form_layout.addRow("冷却时间:", self.cooldown_spin)
        
        # 回复模式
        self.reply_mode_combo = QComboBox()
        self.reply_mode_combo.addItems(["queue", "immediate"])
        self.reply_mode_combo.setCurrentText(self.rule.reply_mode)
        form_layout.addRow("回复模式:", self.reply_mode_combo)
        
        # 回复概率
        self.probability_spin = QSpinBox()
        self.probability_spin.setRange(0, 100)
        self.probability_spin.setValue(int(self.rule.reply_probability * 100))
        self.probability_spin.setSuffix("%")
        form_layout.addRow("回复概率:", self.probability_spin)
        
        layout.addLayout(form_layout)
        
        # 回复模板
        layout.addWidget(QLabel("回复模板（每行一条，支持变量 {user_name} {content} {keyword}）:"))
        self.replies_edit = QTextEdit()
        self.replies_edit.setPlainText('\n'.join(self.rule.replies))
        layout.addWidget(self.replies_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_rule(self) -> tuple:
        """获取规则"""
        keyword = self.keyword_input.text().strip()
        if not keyword:
            return None, None
        
        replies = [r.strip() for r in self.replies_edit.toPlainText().split('\n') if r.strip()]
        if not replies:
            replies = [f"你说了{keyword}"]
        
        rule = KeywordRule(
            keyword=keyword,
            match_type=self.match_type_combo.currentText(),
            replies=replies,
            priority=self.priority_spin.value(),
            cooldown=self.cooldown_spin.value(),
            reply_mode=self.reply_mode_combo.currentText(),
            reply_probability=self.probability_spin.value() / 100.0
        )
        
        return keyword, rule


class KeywordManagerUI(QWidget):
    """关键词管理界面"""
    
    rules_changed = pyqtSignal()  # 规则变更信号
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.rules = {}
        
        self.init_ui()
        self.load_rules()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加关键词")
        self.add_btn.clicked.connect(self.add_keyword)
        toolbar_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑关键词")
        self.edit_btn.clicked.connect(self.edit_keyword)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除关键词")
        self.delete_btn.clicked.connect(self.delete_keyword)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_rules)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 规则表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["关键词", "匹配方式", "优先级", "冷却", "回复模式", "回复数", "触发次数"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.total_count_label = QLabel("总关键词: 0")
        self.total_triggers_label = QLabel("总触发次数: 0")
        stats_layout.addWidget(self.total_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.total_triggers_label)
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
    
    def load_rules(self):
        """加载关键词规则"""
        try:
            keyword_rules = self.config_manager.tts_settings.keyword_rules
            self.rules = {}
            
            for keyword, rule_dict in keyword_rules.items():
                # 将字典转换为KeywordRule对象
                if isinstance(rule_dict, dict):
                    rule = KeywordRule(
                        keyword=keyword,
                        match_type=rule_dict.get('match_type', 'contain'),
                        replies=rule_dict.get('replies', [f"你说了{keyword}"]),
                        priority=rule_dict.get('priority', 1),
                        cooldown=rule_dict.get('cooldown', 10),
                        reply_mode=rule_dict.get('reply_mode', 'queue'),
                        reply_probability=rule_dict.get('reply_probability', 1.0)
                    )
                    self.rules[keyword] = rule
            
            self.update_table()
            g_logger.info(f"加载了 {len(self.rules)} 个关键词规则")
        except Exception as e:
            g_logger.error(f"加载关键词规则失败: {e}")
    
    def update_table(self):
        """更新表格显示"""
        self.table.setRowCount(0)
        
        for keyword, rule in self.rules.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(keyword))
            self.table.setItem(row, 1, QTableWidgetItem(rule.match_type))
            self.table.setItem(row, 2, QTableWidgetItem(str(rule.priority)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{rule.cooldown}秒"))
            self.table.setItem(row, 4, QTableWidgetItem(rule.reply_mode))
            self.table.setItem(row, 5, QTableWidgetItem(str(len(rule.replies))))
            self.table.setItem(row, 6, QTableWidgetItem("0"))  # 触发次数需要从统计获取
        
        self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        self.total_count_label.setText(f"总关键词: {len(self.rules)}")
        # TODO: 从TTS控制器获取触发次数
    
    def on_selection_changed(self):
        """选择改变"""
        has_selection = self.table.selectionModel().hasSelection()
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def add_keyword(self):
        """添加关键词"""
        dialog = KeywordRuleDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            keyword, rule = dialog.get_rule()
            if keyword and rule:
                # 添加到配置
                rule_dict = {
                    'match_type': rule.match_type,
                    'replies': rule.replies,
                    'priority': rule.priority,
                    'cooldown': rule.cooldown,
                    'reply_mode': rule.reply_mode,
                    'reply_probability': rule.reply_probability
                }
                self.config_manager.add_keyword_rule(keyword, rule_dict)
                
                # 更新显示
                self.rules[keyword] = rule
                self.update_table()
                self.rules_changed.emit()
                
                g_logger.info(f"添加关键词规则: {keyword}")
    
    def edit_keyword(self):
        """编辑关键词"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        keyword = self.table.item(row, 0).text()
        rule = self.rules.get(keyword)
        
        if not rule:
            return
        
        dialog = KeywordRuleDialog(keyword, rule, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_keyword, new_rule = dialog.get_rule()
            if new_keyword and new_rule:
                # 如果关键词改变了，删除旧的
                if new_keyword != keyword:
                    self.config_manager.remove_keyword_rule(keyword)
                
                # 更新配置
                rule_dict = {
                    'match_type': new_rule.match_type,
                    'replies': new_rule.replies,
                    'priority': new_rule.priority,
                    'cooldown': new_rule.cooldown,
                    'reply_mode': new_rule.reply_mode,
                    'reply_probability': new_rule.reply_probability
                }
                self.config_manager.update_keyword_rule(new_keyword, rule_dict)
                
                # 更新显示
                if new_keyword != keyword:
                    del self.rules[keyword]
                self.rules[new_keyword] = new_rule
                self.update_table()
                self.rules_changed.emit()
                
                g_logger.info(f"更新关键词规则: {new_keyword}")
    
    def delete_keyword(self):
        """删除关键词"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        keyword = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除关键词 '{keyword}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config_manager.remove_keyword_rule(keyword)
            del self.rules[keyword]
            self.update_table()
            self.rules_changed.emit()
            
            g_logger.info(f"删除关键词规则: {keyword}")