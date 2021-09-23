"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
import os
from napari_plugin_engine import napari_hook_implementation

import qtpy.QtCore
from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFileDialog,
                            QLabel, QTabWidget, QHBoxLayout, QMessageBox)

from scixtracergui.framework import SgAction, SgComponent

from scixtracergui.experiment.states import (SgExperimentHomeStates,
                                             SgExperimentCreateStates,
                                             SgExperimentStates)
from scixtracergui.experiment.containers import (SgExperimentHomeContainer,
                                                 SgExperimentCreateContainer)
from scixtracergui.experiment.components import (SgExperimentHomeComponent,
                                                 SgExperimentCreateComponent)
from scixtracergui.experiment.experiment import SgExperimentComponent
from scixtracergui.experiment.models import SgExperimentCreateModel

from skimage.io import imread
import scixtracer as sx


class SgExperimentApp(SgComponent):
    def __init__(self, napari_viewer):
        super().__init__()

        self.napari_viewer = napari_viewer
        self.req = sx.Request()

        # container
        self.expHomeContainer = SgExperimentHomeContainer()
        self.expCreateContainer = SgExperimentCreateContainer()

        # components
        self.homeComponent = SgExperimentHomeComponent(self.expHomeContainer)
        self.experimentComponent = SgExperimentComponent()
        self.createComponent = SgExperimentCreateComponent(
            self.expCreateContainer)

        # models
        self.experimentModel = SgExperimentCreateModel(self.expCreateContainer)

        # connections
        self.expHomeContainer.register(self)
        self.expCreateContainer.register(self)
        self.experimentComponent.expContainer.register(self)

        # create the widget
        self.widget = QWidget()
        self.widget.setObjectName('SgWidget')
        self.widget.setAttribute(qtpy.QtCore.Qt.WA_StyledBackground, True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.widget.setLayout(layout)

        self.tabWidget = QTabWidget()
        layout.addWidget(self.createComponent.get_widget())
        layout.addWidget(self.homeComponent.get_widget())
        layout.addWidget(self.experimentComponent.get_widget())
        self.createComponent.get_widget().setVisible(False)
        self.experimentComponent.get_widget().setVisible(False)

    def update(self, action: SgAction):
        if action.state == SgExperimentStates.DataDoubleClicked:
            data_info = self.req.get_rawdata(self.experimentComponent.expContainer.selected_data_info.md_uri)
            print('try to open in napari:')
            print('format:', data_info.format)
            print('uri:', data_info.uri)
            self.napari_viewer.add_image(imread(data_info.uri), name=data_info.name)

        if action.state == SgExperimentHomeStates.NewClicked:
            self.createComponent.get_widget().setVisible(True)
            self.homeComponent.get_widget().setVisible(False)
        if action.state == SgExperimentHomeStates.OpenClicked:
            dir_ = QFileDialog.getExistingDirectory(
                self.widget,
                "Open an Experiment folder",
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            self.experimentComponent.load_experiment(
                os.path.join(dir_, 'experiment.md.json'))
            self.homeComponent.get_widget().setVisible(False)
            self.experimentComponent.get_widget().setVisible(True)
        if action.state == SgExperimentCreateStates.ExperimentCreated:
            self.createComponent.get_widget().setVisible(False)
            self.experimentComponent.get_widget().setVisible(True)
        if action.state == SgExperimentCreateStates.ExperimentCreationError:
            msgBox = QMessageBox()
            msgBox.setText(self.expCreateContainer.errorMessage)
            msgBox.exec()

    def get_widget(self):
        return self.widget


class SciXtracer(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        component = SgExperimentApp(napari_viewer)

        dir_path = os.path.dirname(os.path.realpath(__file__))
        stylesheet_path = os.path.join(dir_path, 'theme', 'dark',
                                       'stylesheet.css')
        print('set the stylesheet:', stylesheet_path)
        component.get_widget().setStyleSheet("file:///" + stylesheet_path)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(component.get_widget())


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [SciXtracer]
