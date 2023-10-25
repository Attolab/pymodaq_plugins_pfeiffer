import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

import pylablib as pylablib
from pymodaq_plugins_alcatel.hardware.ACM1000_wrapper import ACM1000


class DAQ_0DViewer_ACM1000(DAQ_Viewer_base):
    """ 
    Instrument plugin class for the Alcatel ACM 1000 gauge controller.

    Compatible instruments: 
    -----------
    - Alcatel ACM 1000 

    Tested with: 
    -----------
    - Alcatel ACM 1000 controller (itself connected to Alcatel ACC 1009 gauges)
    - PyMoDAQ version 4.0.8
    - Windows 10 ver. 21H2

    Installation instructions:
    -----------
    - No drivers from Alcatel are required.
    - Your PC should have serial ports (COM ports) to connect the controller.
      On Windows 10 you may need to install a driver to create virtual COM ports.

    Attributes:
    -----------
    controller: ACM1000 class, based on the pylablib Pfeiffer TPG260 wrapper.
    """
    ports = pylablib.list_backend_resources("serial")
    if ports:
        default_port = ports[0]
    else:
        ports = 'No ports available'
        default_port = 'No ports available'

    params = comon_parameters+[
        {'title': 'Available ports', 'name': 'available_ports', 'type': 'list', 'values': ports, 'readonly': True},
        {'title': 'Selected port', 'name': 'selected_port', 'type': 'str', 'value': default_port}
        ]

    def ini_attributes(self):

        self.controller: ACM1000 = None
        self.hardware_averaging = False

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """

        if param.name() == 'selected_port': # if the selected COM port was changed, try to connect to it
           self.controller.close() 
           self.ini_detector()

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_detector_init(old_controller=controller,
                               new_controller=ACM1000(self.settings['selected_port']))
        
        self.controller.enable_sensors()
        self.init_display()

        initialized = self.controller.test_connection()

        info = 'Initialization...'
        return info, initialized
    
    def init_display(self):
        self.dte_signal_temp.emit(DataToExport(name='ACM1000_to_display',
                                               data=[DataFromPlugins(name='Channel 1', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 1']),
                                                    DataFromPlugins(name='Channel 2', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 2']),
                                                    DataFromPlugins(name='Channel 3', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 3']),
                                                    DataFromPlugins(name='Channel 4', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 4']),
                                                    DataFromPlugins(name='Channel 5', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 5']),
                                                    DataFromPlugins(name='Channel 6', data=[np.array([0.0])],
                                                                    dim='Data0D', labels=['Channel 6'])]))

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()

    def grab_data(self, Naverage=None, **kwargs):
        """
        Start a grab from the detector

        Parameters
        ----------
        """

        data_tot = []
        for channel in [1,2,3,4,5,6]:
            status = self.controller.get_channel_status(channel)
            pressure = self.controller.get_pressure(channel)
            if status in ['ok', 'under', 'over']:
                to_display = self.controller.from_Pa(pressure, units="mbar")
            else:   
                to_display = 0.0
            data_tot.append(DataFromPlugins(name='Channel '+str(channel), data=[np.array([to_display])],
                                                            dim='Data0D', labels=['Channel '+str(channel)+' - Status = '+str(status)]))

        self.dte_signal.emit(DataToExport(name='ACM1000_to_display',
                                        data=data_tot))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.emit_status(ThreadCommand('Update_Status', ['Stopped grabbing']))
        return ''


if __name__ == '__main__':
    main(__file__)
