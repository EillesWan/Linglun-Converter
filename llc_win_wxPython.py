# -*- coding: utf-8 -*-

# 导入所需库
import datetime
import os
import random
import sys
import urllib.error
import urllib.request

import Musicreater
import TrimLog
import wx
from Musicreater.plugin import ConvertConfig
from Musicreater.plugin.bdxfile import (to_BDX_file_in_delay,
                                        to_BDX_file_in_score)
from Musicreater.plugin.funcpack import to_function_addon_in_score
from Musicreater.plugin.mcstructpack import to_mcstructure_addon_in_delay
from TrimLog import Console, object_constants

is_logging: bool = True

osc = object_constants.ObjectStateConstant()
logger = TrimLog.Logger(
    is_logging=is_logging,
    printing=not osc.isRelease,
    in_suffix=".llc",
)

WHITE = (242, 244, 246) # F2F4F6
BLACK = (18, 17, 16) # 121110

try:
    myWords = (
        urllib.request.urlopen(
            'https://gitee.com/TriM-Organization/LinglunStudio/raw/master/resources/myWords.txt'
        )
        .read()
        .decode('utf-8')
        .strip("\n")
        .split("\n")
    )
except (ConnectionError, urllib.error.HTTPError) as E:
    logger.warning(f"读取言·论信息发生 互联网连接 错误：\n{E}")
    myWords = ["以梦想为驱使 创造属于自己的未来"]
# noinspection PyBroadException
except BaseException as E:
    logger.warning(f"读取言·论信息发生 未知 错误：\n{E}")
    myWords = ["灵光焕发 深艺献心"]




# 创建应用程序类
class LinglunConverterApp(wx.App):
    def OnInit(self):
        # 创建主窗口
        self.frame = LinglunConverterFrame(None, title="伶伦转换器")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


# 创建主窗口类
class LinglunConverterFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(LinglunConverterFrame, self).__init__(*args, **kwargs)

        # 设置窗口属性
        self.SetSize((500, 300))
        self.Center()

        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.yanlun_sizer = wx.BoxSizer(wx.HORIZONTAL)
        

        now_word = random.choice(myWords).split("\t——")
        self.yanlun_label_a = wx.StaticText(self.panel, label=now_word[0],style=wx.ALIGN_LEFT)
        self.yanlun_label_a.SetForegroundColour(WHITE)
        self.yanlun_label_a.SetBackgroundColour(BLACK)
        self.yanlun_sizer.Add(self.yanlun_label_a, flag=wx.ALIGN_TOP)

        if len(now_word) > 1:
            self.yanlun_label_b = wx.StaticText(self.panel, label=now_word[1],style=wx.ALIGN_RIGHT)
            self.yanlun_label_b.SetForegroundColour(WHITE)
            self.yanlun_label_b.SetBackgroundColour(BLACK)
            self.yanlun_sizer.Add(self.yanlun_label_b, flag=wx.ALIGN_TOP)
        

        self.main_sizer.Add(self.yanlun_sizer, flag=wx.EXPAND)


        # 文件选择控件
        self.file_picker = wx.FilePickerCtrl(
            self.panel,
            message="选择MIDI文件",
            wildcard="MIDI files (*.mid;*.midi)|*.mid;*.midi",
            style=wx.FLP_USE_TEXTCTRL,
        )
        self.main_sizer.Add(self.file_picker, flag=wx.EXPAND)

        # 输出结果类型下拉选择控件
        self.output_type_dropdown = wx.Choice(
            self.panel, choices=["MCPACK", "BDX", "MCSTRUCTURE"]
        )
        self.main_sizer.Add(wx.StaticText(self.panel, label="输出结果类型："))
        self.main_sizer.Add(self.output_type_dropdown, flag=wx.EXPAND)

        # 播放器类型下拉选择控件
        self.player_type_dropdown = wx.Choice(self.panel, choices=["计分板", "延迟"])
        self.main_sizer.Add(wx.StaticText(self.panel, label="播放器类型："))
        self.main_sizer.Add(self.player_type_dropdown, flag=wx.EXPAND)

        # 音量大小滑动条与数字输入框
        self.volume_slider = wx.Slider(
            self.panel, value=100, minValue=1, maxValue=100, style=wx.SL_HORIZONTAL
        )
        self.volume_text = wx.TextCtrl(self.panel, value="1.0")
        self.main_sizer.Add(wx.StaticText(self.panel, label="音量大小："))
        self.main_sizer.Add(self.volume_slider, flag=wx.EXPAND)
        self.main_sizer.Add(self.volume_text, flag=wx.EXPAND)

        # 速度倍率滑动条与数字输入框
        self.speed_slider = wx.Slider(
            self.panel, value=100, minValue=1, maxValue=100, style=wx.SL_HORIZONTAL
        )
        self.speed_text = wx.TextCtrl(self.panel, value="1.0")
        self.main_sizer.Add(wx.StaticText(self.panel, label="速度倍率："))
        self.main_sizer.Add(self.speed_slider, flag=wx.EXPAND)
        self.main_sizer.Add(self.speed_text, flag=wx.EXPAND)

        # 自动生成进度条勾选框
        self.progressbar_checkbox = wx.CheckBox(self.panel, label="是否自动生成进度条")
        self.main_sizer.Add(self.progressbar_checkbox, flag=wx.EXPAND)

        # 进度条相关控件
        self.whole_style_text = wx.TextCtrl(
            self.panel, value=" %%N [ %%s/%^s %%% __________ %%t|%^t]"
        )
        self.non_played_text = wx.TextCtrl(self.panel, value="§7=§r")
        self.has_played_text = wx.TextCtrl(self.panel, value="§e=§r")
        self.main_sizer.Add(wx.StaticText(self.panel, label="整体样式："))
        self.main_sizer.Add(self.whole_style_text, flag=wx.EXPAND)
        self.main_sizer.Add(wx.StaticText(self.panel, label="动条（未播放）："))
        self.main_sizer.Add(self.non_played_text, flag=wx.EXPAND)
        self.main_sizer.Add(wx.StaticText(self.panel, label="动条（已播放）："))
        self.main_sizer.Add(self.has_played_text, flag=wx.EXPAND)

        # 计分板相关控件
        self.scoreboard_name_text = wx.TextCtrl(self.panel, value="mscply")
        self.auto_reset_checkbox = wx.CheckBox(self.panel, label="是否结束后重置计分板")

        # 延迟相关控件
        self.selecter_text = wx.TextCtrl(self.panel, value="@a")
        self.max_struct_height_slider = wx.Slider(
            self.panel, value=63, minValue=4, maxValue=256, style=wx.SL_HORIZONTAL
        )
        self.max_struct_height_text = wx.TextCtrl(self.panel, value="63")

        # BDX相关控件
        self.author_name_text = wx.TextCtrl(self.panel, value="Unfamous")

        # 导出结果按钮
        self.export_button = wx.Button(self.panel, label="导出结果")

        # 添加控件到主sizer中
        self.main_sizer.Add(self.scoreboard_name_text, flag=wx.EXPAND)
        self.main_sizer.Add(self.auto_reset_checkbox, flag=wx.EXPAND)
        self.main_sizer.Add(self.selecter_text, flag=wx.EXPAND)
        self.main_sizer.Add(self.max_struct_height_slider, flag=wx.EXPAND)
        self.main_sizer.Add(self.max_struct_height_text, flag=wx.EXPAND)
        self.main_sizer.Add(self.author_name_text, flag=wx.EXPAND)
        self.main_sizer.Add(self.export_button, flag=wx.EXPAND)

        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()

        # 绑定事件处理程序
        self.file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_file_selected)
        self.output_type_dropdown.Bind(wx.EVT_CHOICE, self.on_output_type_selected)
        self.player_type_dropdown.Bind(wx.EVT_CHOICE, self.on_player_type_selected)
        self.volume_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_volume_slider_changed)
        self.speed_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_speed_slider_changed)
        self.progressbar_checkbox.Bind(
            wx.EVT_CHECKBOX, self.on_progressbar_checkbox_changed
        )
        self.max_struct_height_slider.Bind(
            wx.EVT_SCROLL_CHANGED, self.on_max_struct_height_slider_changed
        )
        self.export_button.Bind(wx.EVT_BUTTON, self.on_export_button_clicked)

        self.HideUnnecessaryControls()
        self.Layout()

    def HideUnnecessaryControls(self):
        # 隐藏所有不需要显示的控件
        self.scoreboard_name_text.Hide()
        self.auto_reset_checkbox.Hide()
        self.selecter_text.Hide()
        self.max_struct_height_slider.Hide()
        self.max_struct_height_text.Hide()
        self.author_name_text.Hide()
        self.whole_style_text.Hide()
        self.non_played_text.Hide()
        self.has_played_text.Hide()
        self.Layout()

    def on_file_selected(self, event):
        file_to_convert = self.file_picker.GetPath()
        # 处理选择的文件

    def on_output_type_selected(self, event):
        output_type = self.output_type_dropdown.GetStringSelection()
        # 处理选择的输出结果类型

    def on_player_type_selected(self, event):
        player_type = self.player_type_dropdown.GetStringSelection()
        if player_type == "计分板":
            # 显示计分板相关控件
            self.scoreboard_name_text.Show()
            self.auto_reset_checkbox.Show()
            # 隐藏延迟相关控件
            self.selecter_text.Hide()
            self.max_struct_height_slider.Hide()
            self.max_struct_height_text.Hide()
        elif player_type == "延迟":
            # 显示延迟相关控件
            self.selecter_text.Show()
            self.max_struct_height_slider.Show()
            self.max_struct_height_text.Show()
            # 隐藏计分板相关控件
            self.scoreboard_name_text.Hide()
            self.auto_reset_checkbox.Hide()
        self.Layout()

    def on_volume_slider_changed(self, event):
        volume = self.volume_slider.GetValue()
        self.volume_text.SetValue(str(volume / 100))  # 更新音量大小输入框的值

    def on_speed_slider_changed(self, event):
        speed = self.speed_slider.GetValue()
        self.speed_text.SetValue(str(speed / 100))  # 更新速度倍率输入框的值

    def on_progressbar_checkbox_changed(self, event):
        is_progressbar_selected = self.progressbar_checkbox.GetValue()
        if is_progressbar_selected:
            # 显示进度条相关控件
            self.whole_style_text.Show()
            self.non_played_text.Show()
            self.has_played_text.Show()
        else:
            # 隐藏进度条相关控件
            self.whole_style_text.Hide()
            self.non_played_text.Hide()
            self.has_played_text.Hide()
        self.Layout()

    def on_max_struct_height_slider_changed(self, event):
        max_struct_height = self.max_struct_height_slider.GetValue()
        self.max_struct_height_text.SetValue(str(max_struct_height))  # 更新结构最大高度输入框的值

    def on_export_button_clicked(self, event):
        output_path = wx.DirSelector(message="选择一个文件夹")  # 选择文件夹并保存至output_path变量
        # 导出结果的操作

    class TextCtrlRedirector:
        def __init__(self, text_ctrl):
            self.text_ctrl = text_ctrl

        def write(self, text):
            wx.CallAfter(self.text_ctrl.WriteText, text)

        def flush(self):
            pass


# 启动应用程序
if __name__ == "__main__":
    app = LinglunConverterApp()
    app.MainLoop()
