# 商城窗口

import sys
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QSpinBox, QComboBox, QMessageBox, QHeaderView,
    QFrame, QScrollArea, QGridLayout, QDialog, QLineEdit, QTextEdit,
    QMainWindow, QMenuBar, QStatusBar, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

from client.network.api_client import GameAPIClient, APIException
from client.state_manager import get_state_manager
from shared.constants import ITEM_QUALITY


class ShopDataWorker(QThread):
    """商城数据加载工作线程"""
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: GameAPIClient):
        super().__init__()
        self.api_client = api_client

    def run(self):
        """加载商城数据"""
        try:
            result = self.api_client.shop.get_shop_info()
            if result.get('success'):
                self.data_loaded.emit(result.get('data', {}))
            else:
                self.error_occurred.emit(result.get('message', '获取商城数据失败'))
        except APIException as e:
            self.error_occurred.emit(f"网络错误: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"未知错误: {str(e)}")


class PurchaseDialog(QDialog):
    """购买物品对话框"""

    def __init__(self, parent=None, item_data=None, user_currency=None):
        super().__init__(parent)
        self.item_data = item_data or {}
        self.user_currency = user_currency or {}
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        item_info = self.item_data.get('item_info', {})
        item_name = item_info.get('name', '未知物品')
        price = self.item_data.get('price', 0)
        currency_type = self.item_data.get('currency_type', 'gold')
        currency_name = "金币" if currency_type == "gold" else "灵石"

        self.setWindowTitle(f"购买 - {item_name}")
        self.setFixedSize(350, 250)
        self.setModal(True)

        layout = QVBoxLayout()

        # 物品信息
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"物品: {item_name}"))
        info_layout.addWidget(QLabel(f"单价: {price} {currency_name}"))

        # 显示物品描述
        description = item_info.get('description', '暂无描述')
        desc_label = QLabel(f"描述: {description}")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)

        # 数量选择
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("购买数量:"))

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.update_total)
        quantity_layout.addWidget(self.quantity_spin)

        layout.addLayout(quantity_layout)

        # 合计信息
        self.total_label = QLabel()
        layout.addWidget(self.total_label)

        # 用户余额
        user_balance = self.user_currency.get(currency_type, 0)
        self.balance_label = QLabel(f"您的余额: {user_balance} {currency_name}")
        layout.addWidget(self.balance_label)

        # 按钮
        button_layout = QHBoxLayout()

        self.confirm_btn = QPushButton("确认购买")
        self.confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 初始化合计
        self.update_total()

    def update_total(self):
        """更新合计金额"""
        quantity = self.quantity_spin.value()
        price = self.item_data.get('price', 0)
        total = quantity * price
        currency_type = self.item_data.get('currency_type', 'gold')
        currency_name = "金币" if currency_type == "gold" else "灵石"

        self.total_label.setText(f"合计: {total} {currency_name}")

        # 检查余额是否足够
        user_balance = self.user_currency.get(currency_type, 0)
        if total > user_balance:
            self.total_label.setStyleSheet("color: red;")
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setText("余额不足")
        else:
            self.total_label.setStyleSheet("color: green;")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setText("确认购买")

    def get_purchase_data(self):
        """获取购买数据"""
        return {
            'shop_item_id': self.item_data.get('id'),
            'quantity': self.quantity_spin.value()
        }


class CreateTradeDialog(QDialog):
    """创建交易对话框"""

    def __init__(self, parent=None, inventory_items=None):
        super().__init__(parent)
        self.inventory_items = inventory_items or []
        self.selected_item = None
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("创建交易")
        self.setFixedSize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout()

        # 物品选择
        item_layout = QHBoxLayout()
        item_layout.addWidget(QLabel("选择物品:"))

        self.item_combo = QComboBox()
        self.item_combo.addItem("请选择物品", None)
        for item in self.inventory_items:
            if item.get('quantity', 0) > 0:
                item_name = item.get('item_info', {}).get('name', '未知物品')
                quantity = item.get('quantity', 0)
                self.item_combo.addItem(f"{item_name} (x{quantity})", item)

        item_layout.addWidget(self.item_combo)
        layout.addLayout(item_layout)

        # 数量选择
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("数量:"))

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1)
        quantity_layout.addWidget(self.quantity_spin)

        layout.addLayout(quantity_layout)

        # 价格设置
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("价格:"))

        self.price_spin = QSpinBox()
        self.price_spin.setMinimum(1)
        self.price_spin.setMaximum(999999999)
        self.price_spin.setValue(100)
        price_layout.addWidget(self.price_spin)

        layout.addLayout(price_layout)

        # 货币类型
        currency_layout = QHBoxLayout()
        currency_layout.addWidget(QLabel("货币类型:"))

        self.currency_combo = QComboBox()
        self.currency_combo.addItem("金币", "gold")
        self.currency_combo.addItem("灵石", "spirit_stone")
        currency_layout.addWidget(self.currency_combo)

        layout.addLayout(currency_layout)

        # 按钮
        button_layout = QHBoxLayout()

        confirm_btn = QPushButton("确认创建")
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 连接信号
        self.item_combo.currentIndexChanged.connect(self.on_item_changed)

    def on_item_changed(self):
        """物品选择变化"""
        item_data = self.item_combo.currentData()
        if item_data:
            max_quantity = item_data.get('quantity', 1)
            self.quantity_spin.setMaximum(max_quantity)
            self.quantity_spin.setValue(min(1, max_quantity))
            self.selected_item = item_data
        else:
            self.quantity_spin.setMaximum(1)
            self.quantity_spin.setValue(1)
            self.selected_item = None

    def get_trade_data(self):
        """获取交易数据"""
        if not self.selected_item:
            return None

        return {
            'item_id': self.selected_item.get('item_info', {}).get('id'),
            'quantity': self.quantity_spin.value(),
            'price': self.price_spin.value(),
            'currency_type': self.currency_combo.currentData()
        }


class ShopWindow(QMainWindow):
    """商城窗口 - 独立窗口应用"""

    def __init__(self, parent=None, api_client=None):
        # 如果parent不是QWidget类型，则设为None
        if parent and not hasattr(parent, 'inherits'):
            # parent不是Qt对象，提取api_client并设parent为None
            api_client = getattr(parent, 'api_client', api_client)
            parent = None

        super().__init__(parent)
        self.parent_window = parent
        self.api_client = api_client or (parent.api_client if parent and hasattr(parent, 'api_client') else None)
        self.state_manager = get_state_manager()

        # 数据
        self.shop_data = {}
        self.inventory_data = []

        # 工作线程
        self.data_worker = None

        self.init_ui()
        self.setup_connections()

        # 延迟加载数据
        QTimer.singleShot(500, self.load_shop_data)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("🏪 气运修仙 - 商城")
        self.setFixedSize(650, 600)  # 更加紧凑的窗口尺寸

        # 设置窗口图标（如果有的话）
        # self.setWindowIcon(QIcon("path/to/shop_icon.png"))

        # 创建菜单栏
        self.create_menu_bar()

        # 创建工具栏
        self.create_tool_bar()

        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 系统商城标签页
        self.system_shop_tab = self.create_system_shop_tab()
        self.tab_widget.addTab(self.system_shop_tab, "系统商城")

        # 玩家交易所标签页
        self.player_trade_tab = self.create_player_trade_tab()
        self.tab_widget.addTab(self.player_trade_tab, "玩家交易所")

        # 我的交易标签页
        self.my_trade_tab = self.create_my_trade_tab()
        self.tab_widget.addTab(self.my_trade_tab, "我的交易")

        main_layout.addWidget(self.tab_widget)

        central_widget.setLayout(main_layout)

        # 创建状态栏
        self.create_status_bar()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')

        # 刷新动作
        refresh_action = file_menu.addAction('刷新(&R)')
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.load_shop_data)

        file_menu.addSeparator()

        # 关闭动作
        close_action = file_menu.addAction('关闭(&C)')
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close)

        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')

        # 切换到系统商城
        system_shop_action = view_menu.addAction('系统商城(&S)')
        system_shop_action.setShortcut('Ctrl+1')
        system_shop_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))

        # 切换到玩家交易所
        player_trade_action = view_menu.addAction('玩家交易所(&P)')
        player_trade_action.setShortcut('Ctrl+2')
        player_trade_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))

        # 切换到我的交易
        my_trade_action = view_menu.addAction('我的交易(&M)')
        my_trade_action.setShortcut('Ctrl+3')
        my_trade_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')

        # 关于动作
        about_action = help_menu.addAction('关于商城(&A)')
        about_action.triggered.connect(self.show_about)

    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setMovable(False)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.load_shop_data)
        self.refresh_btn.setToolTip("刷新商城数据 (F5)")
        toolbar.addWidget(self.refresh_btn)

        toolbar.addSeparator()

        # 创建交易按钮
        self.create_trade_btn = QPushButton("📦 创建交易")
        self.create_trade_btn.clicked.connect(self.create_trade)
        self.create_trade_btn.setToolTip("创建新的玩家交易")
        toolbar.addWidget(self.create_trade_btn)

        toolbar.addSeparator()

        # 我的交易按钮
        my_trades_btn = QPushButton("📋 我的交易")
        my_trades_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        my_trades_btn.setToolTip("查看我的交易列表")
        toolbar.addWidget(my_trades_btn)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("欢迎来到气运修仙商城！")

        # 添加永久状态信息
        self.connection_status = QLabel("🟢 已连接")
        self.status_bar.addPermanentWidget(self.connection_status)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于商城",
            "气运修仙 - 商城系统\n\n"
            "版本: 1.0.0\n"
            "功能:\n"
            "• 系统商城 - 购买基础物品和装备\n"
            "• 玩家交易所 - 玩家间自由交易\n"
            "• 我的交易 - 管理个人交易\n\n"
            "快捷键:\n"
            "• F5: 刷新\n"
            "• Ctrl+W: 关闭\n"
            "• Ctrl+1/2/3: 切换标签页"
        )

    def create_system_shop_tab(self) -> QWidget:
        """创建系统商城标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 商品表格
        self.system_shop_table = QTableWidget()
        self.system_shop_table.setColumnCount(8)
        self.system_shop_table.setHorizontalHeaderLabels([
            "物品名称", "品质", "类型", "价格", "货币", "库存", "详情", "操作"
        ])

        # 设置表格属性
        header = self.system_shop_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # 物品名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 品质
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 价格
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 货币
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 库存
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 详情
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 操作

        # 设置列宽 - 紧凑布局
        self.system_shop_table.setColumnWidth(0, 100)  # 物品名称
        self.system_shop_table.setColumnWidth(1, 40)   # 品质
        self.system_shop_table.setColumnWidth(2, 60)   # 类型
        self.system_shop_table.setColumnWidth(3, 50)   # 价格
        self.system_shop_table.setColumnWidth(4, 40)   # 货币
        self.system_shop_table.setColumnWidth(5, 40)   # 库存
        self.system_shop_table.setColumnWidth(6, 50)   # 详情
        self.system_shop_table.setColumnWidth(7, 50)   # 操作

        # 表格设置
        self.system_shop_table.setAlternatingRowColors(True)
        self.system_shop_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # 移除选中效果
        self.system_shop_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 设置为不可编辑

        layout.addWidget(self.system_shop_table)
        widget.setLayout(layout)
        return widget

    def create_player_trade_tab(self) -> QWidget:
        """创建玩家交易所标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 交易表格
        self.player_trade_table = QTableWidget()
        self.player_trade_table.setColumnCount(8)
        self.player_trade_table.setHorizontalHeaderLabels([
            "卖家", "物品名称", "品质", "数量", "价格", "货币", "发布时间", "操作"
        ])

        # 设置表格属性
        header = self.player_trade_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 卖家
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)       # 物品名称
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 品质
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 数量
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 价格
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 货币
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 发布时间
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 操作

        # 设置列宽 - 紧凑布局
        self.player_trade_table.setColumnWidth(0, 70)   # 卖家
        self.player_trade_table.setColumnWidth(1, 110)  # 物品名称
        self.player_trade_table.setColumnWidth(2, 50)   # 品质
        self.player_trade_table.setColumnWidth(3, 40)   # 数量
        self.player_trade_table.setColumnWidth(4, 60)   # 价格
        self.player_trade_table.setColumnWidth(5, 45)   # 货币
        self.player_trade_table.setColumnWidth(6, 80)   # 发布时间
        self.player_trade_table.setColumnWidth(7, 60)   # 操作

        self.player_trade_table.setAlternatingRowColors(True)
        self.player_trade_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.player_trade_table)
        widget.setLayout(layout)
        return widget

    def create_my_trade_tab(self) -> QWidget:
        """创建我的交易标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 我的交易表格
        self.my_trade_table = QTableWidget()
        self.my_trade_table.setColumnCount(8)
        self.my_trade_table.setHorizontalHeaderLabels([
            "物品名称", "品质", "数量", "价格", "货币", "状态", "发布时间", "操作"
        ])

        # 设置表格属性
        header = self.my_trade_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)       # 物品名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 品质
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 数量
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 价格
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 货币
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 发布时间
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 操作

        # 设置列宽 - 紧凑布局
        self.my_trade_table.setColumnWidth(0, 110)  # 物品名称
        self.my_trade_table.setColumnWidth(1, 50)   # 品质
        self.my_trade_table.setColumnWidth(2, 40)   # 数量
        self.my_trade_table.setColumnWidth(3, 60)   # 价格
        self.my_trade_table.setColumnWidth(4, 45)   # 货币
        self.my_trade_table.setColumnWidth(5, 60)   # 状态
        self.my_trade_table.setColumnWidth(6, 80)   # 发布时间
        self.my_trade_table.setColumnWidth(7, 60)   # 操作

        self.my_trade_table.setAlternatingRowColors(True)
        self.my_trade_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.my_trade_table)
        widget.setLayout(layout)
        return widget

    def setup_connections(self):
        """设置信号连接"""
        pass

    def load_shop_data(self):
        """加载商城数据"""
        if not self.api_client:
            QMessageBox.warning(self, "错误", "API客户端未初始化")
            return

        # 停止之前的工作线程
        if self.data_worker and self.data_worker.isRunning():
            self.data_worker.quit()
            self.data_worker.wait()

        # 创建新的工作线程
        self.data_worker = ShopDataWorker(self.api_client)
        self.data_worker.data_loaded.connect(self.on_shop_data_loaded)
        self.data_worker.error_occurred.connect(self.on_data_error)
        self.data_worker.start()

        # 禁用刷新按钮
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("🔄 加载中...")

        # 更新状态栏
        self.status_bar.showMessage("正在加载商城数据...")

    def on_shop_data_loaded(self, data: Dict[str, Any]):
        """商城数据加载完成"""
        self.shop_data = data

        # 更新界面
        self.update_system_shop_table()
        self.update_player_trade_table()

        # 加载背包数据用于创建交易
        self.load_inventory_data()

        # 恢复刷新按钮
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")

        # 更新状态栏
        system_count = len(data.get('system_items', []))
        trade_count = len(data.get('player_trades', []))
        self.status_bar.showMessage(f"商城数据加载完成 - 系统商品: {system_count} 个，玩家交易: {trade_count} 个")

    def on_data_error(self, error_msg: str):
        """数据加载错误"""
        QMessageBox.warning(self, "错误", f"加载商城数据失败: {error_msg}")

        # 恢复刷新按钮
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")

        # 更新状态栏
        self.status_bar.showMessage("加载商城数据失败")

    def load_inventory_data(self):
        """加载背包数据"""
        try:
            if self.api_client:
                result = self.api_client.inventory.get_inventory()
                if result.get('success'):
                    self.inventory_data = result.get('data', {}).get('items', [])
        except Exception as e:
            print(f"加载背包数据失败: {e}")

    def update_system_shop_table(self):
        """更新系统商城表格"""
        system_items = self.shop_data.get('system_items', [])
        self.system_shop_table.setRowCount(len(system_items))

        for row, item in enumerate(system_items):
            item_info = item.get('item_info', {})

            # 物品名称
            name_item = QTableWidgetItem(item_info.get('name', ''))
            self.system_shop_table.setItem(row, 0, name_item)

            # 品质
            quality = item_info.get('quality', 'COMMON')
            quality_item = QTableWidgetItem(ITEM_QUALITY.get(quality, {}).get('name', quality))
            quality_color = QColor(ITEM_QUALITY.get(quality, {}).get('color', '#000000'))
            quality_item.setForeground(quality_color)
            self.system_shop_table.setItem(row, 1, quality_item)

            # 类型
            item_type = item_info.get('item_type', '')
            type_item = QTableWidgetItem(item_type)
            self.system_shop_table.setItem(row, 2, type_item)

            # 价格
            price_item = QTableWidgetItem(str(item.get('price', 0)))
            self.system_shop_table.setItem(row, 3, price_item)

            # 货币
            currency = "金币" if item.get('currency_type') == "gold" else "灵石"
            currency_item = QTableWidgetItem(currency)
            self.system_shop_table.setItem(row, 4, currency_item)

            # 库存
            stock = item.get('stock', -1)
            stock_text = "无限" if stock == -1 else str(stock)
            stock_item = QTableWidgetItem(stock_text)
            self.system_shop_table.setItem(row, 5, stock_item)

            # 详情按钮
            detail_btn = QPushButton("详情")
            detail_btn.clicked.connect(lambda checked, item_data=item: self.show_item_detail(item_data))
            self.system_shop_table.setCellWidget(row, 6, detail_btn)

            # 操作按钮
            buy_btn = QPushButton("购买")
            buy_btn.clicked.connect(lambda checked, item_data=item: self.buy_system_item(item_data))
            self.system_shop_table.setCellWidget(row, 7, buy_btn)

    def update_player_trade_table(self):
        """更新玩家交易表格"""
        player_trades = self.shop_data.get('player_trades', [])
        self.player_trade_table.setRowCount(len(player_trades))

        for row, trade in enumerate(player_trades):
            item_info = trade.get('item_info', {})

            # 卖家
            seller_item = QTableWidgetItem(trade.get('seller_name', ''))
            self.player_trade_table.setItem(row, 0, seller_item)

            # 物品名称
            name_item = QTableWidgetItem(item_info.get('name', ''))
            self.player_trade_table.setItem(row, 1, name_item)

            # 品质
            quality = item_info.get('quality', 'COMMON')
            quality_item = QTableWidgetItem(ITEM_QUALITY.get(quality, {}).get('name', quality))
            quality_color = QColor(ITEM_QUALITY.get(quality, {}).get('color', '#000000'))
            quality_item.setForeground(quality_color)
            self.player_trade_table.setItem(row, 2, quality_item)

            # 数量
            quantity_item = QTableWidgetItem(str(trade.get('quantity', 1)))
            self.player_trade_table.setItem(row, 3, quantity_item)

            # 价格
            price_item = QTableWidgetItem(str(trade.get('price', 0)))
            self.player_trade_table.setItem(row, 4, price_item)

            # 货币
            currency = "金币" if trade.get('currency_type') == "gold" else "灵石"
            currency_item = QTableWidgetItem(currency)
            self.player_trade_table.setItem(row, 5, currency_item)

            # 发布时间
            created_at = trade.get('created_at', '')
            if created_at:
                # 简化时间显示
                time_str = created_at.split('T')[0] if 'T' in created_at else created_at
                time_item = QTableWidgetItem(time_str)
                self.player_trade_table.setItem(row, 6, time_item)

            # 操作按钮
            buy_btn = QPushButton("购买")
            buy_btn.clicked.connect(lambda checked, trade_data=trade: self.buy_player_trade(trade_data))
            self.player_trade_table.setCellWidget(row, 7, buy_btn)

    def show_item_detail(self, item_data: Dict[str, Any]):
        """显示物品详情"""
        item_info = item_data.get('item_info', {})
        name = item_info.get('name', '未知物品')
        description = item_info.get('description', '暂无描述')
        item_type = item_info.get('item_type', '未知类型')
        quality = item_info.get('quality', 'COMMON')
        quality_name = ITEM_QUALITY.get(quality, {}).get('name', quality)

        # 构建详情文本
        detail_text = f"""
物品名称: {name}
物品类型: {item_type}
品质等级: {quality_name}
物品描述: {description}

价格: {item_data.get('price', 0)} {"金币" if item_data.get('currency_type') == 'gold' else "灵石"}
库存: {"无限" if item_data.get('stock', -1) == -1 else str(item_data.get('stock', 0))}
        """.strip()

        QMessageBox.information(self, f"物品详情 - {name}", detail_text)

    def buy_system_item(self, item_data: Dict[str, Any]):
        """购买系统商城物品"""
        try:
            # 获取用户货币信息
            user_currency = {}
            if hasattr(self, 'parent_window') and self.parent_window:
                # 尝试从父窗口获取角色信息
                try:
                    char_result = self.api_client.user.get_character_detail()
                    if char_result.get('success'):
                        char_data = char_result.get('data', {})
                        user_currency = {
                            'gold': char_data.get('gold', 0),
                            'spirit_stone': char_data.get('spirit_stone', 0)
                        }
                except:
                    user_currency = {'gold': 0, 'spirit_stone': 0}

            # 显示购买对话框
            dialog = PurchaseDialog(self, item_data, user_currency)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                purchase_data = dialog.get_purchase_data()

                result = self.api_client.shop.purchase_system_item(
                    purchase_data['shop_item_id'],
                    purchase_data['quantity']
                )

                if result.get('success'):
                    QMessageBox.information(self, "成功", result.get('message', '购买成功'))
                    # 刷新数据
                    self.load_shop_data()
                    # 通知父窗口刷新角色信息
                    if self.parent_window and hasattr(self.parent_window, 'character_info_widget'):
                        self.parent_window.character_info_widget.refresh_character_info()
                else:
                    QMessageBox.warning(self, "失败", result.get('message', '购买失败'))

        except APIException as e:
            QMessageBox.warning(self, "网络错误", f"购买失败: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"购买失败: {str(e)}")

    def buy_player_trade(self, trade_data: Dict[str, Any]):
        """购买玩家交易物品"""
        try:
            item_info = trade_data.get('item_info', {})
            item_name = item_info.get('name', '未知物品')
            quantity = trade_data.get('quantity', 1)
            price = trade_data.get('price', 0)
            currency = "金币" if trade_data.get('currency_type') == "gold" else "灵石"
            seller_name = trade_data.get('seller_name', '未知卖家')

            # 确认购买
            reply = QMessageBox.question(
                self, "确认购买",
                f"确定要花费 {price} {currency} 从 {seller_name} 购买 {quantity} 个 {item_name} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                result = self.api_client.shop.buy_trade(trade_data.get('id'))

                if result.get('success'):
                    QMessageBox.information(self, "成功", result.get('message', '购买成功'))
                    # 刷新数据
                    self.load_shop_data()
                    # 通知父窗口刷新角色信息
                    if self.parent_window and hasattr(self.parent_window, 'character_info_widget'):
                        self.parent_window.character_info_widget.refresh_character_info()
                else:
                    QMessageBox.warning(self, "失败", result.get('message', '购买失败'))

        except APIException as e:
            QMessageBox.warning(self, "网络错误", f"购买失败: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"购买失败: {str(e)}")

    def create_trade(self):
        """创建交易"""
        if not self.inventory_data:
            QMessageBox.information(self, "提示", "背包中没有可交易的物品")
            return

        dialog = CreateTradeDialog(self, self.inventory_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trade_data = dialog.get_trade_data()
            if trade_data:
                try:
                    result = self.api_client.shop.create_trade(**trade_data)

                    if result.get('success'):
                        QMessageBox.information(self, "成功", result.get('message', '创建交易成功'))
                        # 刷新数据
                        self.load_shop_data()
                        # 切换到我的交易标签页
                        self.tab_widget.setCurrentIndex(2)
                        self.load_my_trades()
                    else:
                        QMessageBox.warning(self, "失败", result.get('message', '创建交易失败'))

                except APIException as e:
                    QMessageBox.warning(self, "网络错误", f"创建交易失败: {str(e)}")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"创建交易失败: {str(e)}")

    def load_my_trades(self):
        """加载我的交易"""
        try:
            if self.api_client:
                result = self.api_client.shop.get_my_trades()
                if result.get('success'):
                    trades = result.get('data', {}).get('trades', [])
                    self.update_my_trade_table(trades)
        except Exception as e:
            print(f"加载我的交易失败: {e}")

    def update_my_trade_table(self, trades: List[Dict[str, Any]]):
        """更新我的交易表格"""
        self.my_trade_table.setRowCount(len(trades))

        for row, trade in enumerate(trades):
            item_info = trade.get('item_info', {})

            # 物品名称
            name_item = QTableWidgetItem(item_info.get('name', ''))
            self.my_trade_table.setItem(row, 0, name_item)

            # 品质
            quality = item_info.get('quality', 'COMMON')
            quality_item = QTableWidgetItem(ITEM_QUALITY.get(quality, {}).get('name', quality))
            quality_color = QColor(ITEM_QUALITY.get(quality, {}).get('color', '#000000'))
            quality_item.setForeground(quality_color)
            self.my_trade_table.setItem(row, 1, quality_item)

            # 数量
            quantity_item = QTableWidgetItem(str(trade.get('quantity', 1)))
            self.my_trade_table.setItem(row, 2, quantity_item)

            # 价格
            price_item = QTableWidgetItem(str(trade.get('price', 0)))
            self.my_trade_table.setItem(row, 3, price_item)

            # 货币
            currency = "金币" if trade.get('currency_type') == "gold" else "灵石"
            currency_item = QTableWidgetItem(currency)
            self.my_trade_table.setItem(row, 4, currency_item)

            # 状态
            status = trade.get('status', 'ACTIVE')
            status_text = {"ACTIVE": "进行中", "SOLD": "已售出", "CANCELLED": "已取消"}.get(status, status)
            status_item = QTableWidgetItem(status_text)
            if status == "SOLD":
                status_item.setForeground(QColor("#28a745"))
            elif status == "CANCELLED":
                status_item.setForeground(QColor("#dc3545"))
            self.my_trade_table.setItem(row, 5, status_item)

            # 发布时间
            created_at = trade.get('created_at', '')
            if created_at:
                time_str = created_at.split('T')[0] if 'T' in created_at else created_at
                time_item = QTableWidgetItem(time_str)
                self.my_trade_table.setItem(row, 6, time_item)

            # 操作按钮
            if status == "ACTIVE":
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(lambda checked, trade_data=trade: self.cancel_trade(trade_data))
                self.my_trade_table.setCellWidget(row, 7, cancel_btn)
            else:
                # 已完成的交易不显示操作按钮
                empty_widget = QWidget()
                self.my_trade_table.setCellWidget(row, 7, empty_widget)

    def cancel_trade(self, trade_data: Dict[str, Any]):
        """取消交易"""
        try:
            item_info = trade_data.get('item_info', {})
            item_name = item_info.get('name', '未知物品')
            quantity = trade_data.get('quantity', 1)

            # 确认取消
            reply = QMessageBox.question(
                self, "确认取消",
                f"确定要取消 {quantity} 个 {item_name} 的交易吗？\n物品将返回到背包中。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                result = self.api_client.shop.cancel_trade(trade_data.get('id'))

                if result.get('success'):
                    QMessageBox.information(self, "成功", result.get('message', '取消交易成功'))
                    # 刷新我的交易
                    self.load_my_trades()
                else:
                    QMessageBox.warning(self, "失败", result.get('message', '取消交易失败'))

        except APIException as e:
            QMessageBox.warning(self, "网络错误", f"取消交易失败: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"取消交易失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止工作线程
        if self.data_worker and self.data_worker.isRunning():
            self.data_worker.quit()
            self.data_worker.wait()
        event.accept()
