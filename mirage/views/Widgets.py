import math

from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog
from PyQt5 import uic

from astropy import units as u



class UserInputWidget(QWidget):
    """docstring for ParametersView"""


    def __init__(self):
        from os import environ
        prefix = None
        if "MIRAGE_HOME" in environ:
            prefix = environ['MIRAGE_HOME']+"/mirage/views/qml/"
        else:
            prefix = ""
        QWidget.__init__(self)
        uic.loadUi(prefix+self.qml,self)

    @property    
    def qml(self):
        pass

    # @abstractproperty
    def actionTriggers(self):
      pass

    # @abstractmethod
    def get_object(self,*args,**kwargs):
        pass

    # @abstractmethod
    def set_object(self,obj,*args,**kwargs):
      pass

    @staticmethod
    def unitFromString(unit_name, r_g, theta_E):
        if unit_name == "uas":
            return u.uas
        elif unit_name == "R_G":
            return r_g
        elif unit_name == "Theta_E":
            return theta_E
        elif unit_name == "arcsec":
            return u.arcsec

    @staticmethod
    def warn_user(message):
        QMessageBox.warning(None, "Warning", message)

class ParametersWidget(UserInputWidget):

    def __init__(self):
        UserInputWidget.__init__(self)
        from random import randint
        self.starSeedRandomizer.clicked.connect(
            lambda : self.imfSeedInput.setValue(randint(1,999999999)))
        self.imfInput.currentTextChanged.connect(
            lambda txt: self.customStarGenBox.setEnabled(txt == "Custom"))
        self.enableMicrolensing.toggled.connect(
            lambda v: self.customStarGenBox.setEnabled(v and self.imfInput.currentText() == "Custom"))

    @property
    def qml(self):
        return "parametersview.ui"

    @staticmethod
    def _mk_mass_fn(powerString,stepString,ageString):
        powers = [float(p) for p in powerString.split(" ")]
        steps = [float(s) for s in stepString.split(" ")]
        if ageString != "":
            conversions = {float(k):float(v) for (k,v) in [s.split(":") for s in ageString.split(" ")]}
            ret =  {"powers":powers,"conversions":conversions,"mass_limits":steps}
            return ret
        else:
            ret = {"powers":powers,"mass_limits":steps}
            return ret

    def get_object(self,*args,**kwargs):
        from mirage.parameters import Parameters, MicrolensingParameters, Quasar, Lens
        from mirage.util import Vec2D, PolarVec, PixelRegion, zero_vector
        from mirage.calculator import getMassFunction
        #First, pull out everyhing a micro and macro object needs.
        #Pull out values for special units first
        try:
            lRedshift = self.lRedshiftInput.value()
            qRedshift = self.qRedshiftInput.value()
            qMass = self.qMassInput.value()*u.solMass
            vDispersion = self.vDispersionInput.value()*u.km/u.s
            r_g, theta_E, xi = Parameters.special_units(qRedshift,lRedshift,qMass)
            einstein_radius = Parameters.static_einstein_radius(vDispersion,qRedshift,lRedshift)
            with u.add_enabled_units([r_g,theta_E,einstein_radius]):
            #Now I can continue to pull out values and not have a unit problem.
                ellipR, ellipTheta = self.ellipRInput.value(), self.ellipThetaInput.value()
                shearR, shearTheta = self.shearRInput.value(), self.shearThetaInput.value()
                qRadius = self.qRadiusInput.value()*UserInputWidget.unitFromString(
                    self.qRadiusUnit.currentText(),r_g,theta_E)
                rayRegionLength = self.rootRayInput.value()
                shear = PolarVec(shearR,shearTheta)
                ellip = PolarVec(ellipR, ellipTheta)
                lens = Lens(lRedshift, vDispersion, shear, ellip)
                quasar = Quasar(qRedshift, qRadius, qMass)
                rayRegion = PixelRegion(zero_vector('arcsec'),
                    Vec2D(1.4,1.4,einstein_radius),
                    Vec2D(rayRegionLength,rayRegionLength))
                macro_parameters = Parameters(quasar,lens,rayRegion)
                if self.enableMicrolensing.isChecked():
                    x,y = [float(v) for v in self.imgLocInput.text()[1:-1].split(",")]
                    imgLocation = Vec2D(x,y,'arcsec')
                    minorAxis = self.sPlaneDimInput.value()*UserInputWidget.unitFromString(
                        self.sPlaneDimUnit.currentText(),r_g,theta_E)
                    mass_fn = None
                    mass_fn_seed = self.imfSeedInput.value()
                    if self.imfInput.currentText() == "Custom":
                        mass_fn = ParametersWidget._mk_mass_fn(self.imfPowersInput.text(),
                            self.imfStepsInput.text(),
                            self.imfAgingInput.text())
                    else:
                        mass_fn = self.imfInput.currentText()
                    star_generator = getMassFunction(mass_fn_seed,mass_fn)
                    micro_params = macro_parameters.to_microParams(self.pcntStarsInput.value(),
                                                                   imgLocation,
                                                                   minorAxis,
                                                                   star_generator)
                    return micro_params
                else:
                    return macro_parameters
        except:
            UserInputWidget.warn_user("Error constructing the Parameters object. Please validate input and try again.")

    def actionTriggers(self):
        from PyQt5 import QtWidgets
        from mirage.io import ParametersFileManager, MicroParametersFileManager
        from mirage.parameters import MicrolensingParameters, Parameters
        def save_action():
            obj = self.get_object()
            fm = None
            if isinstance(obj,MicrolensingParameters):
                fm = MicroParametersFileManager()
            else:
                fm = ParametersFileManager()
            filename = QtWidgets.QFileDialog.getSaveFileName(filter='*'+fm.extension)[0]
            if filename:
                fm.open(filename)
                fm.write(obj)
                print("%s saved." + filename)
                fm.close()

        def open_action():
            from mirage import io
            filename = QtWidgets.QFileDialog.getOpenFileName(filter='*')[0]#'*.param, *.sim, *.res, *.mp')[0]
            params = io.open_parameters(filename)
            if params is not None:
                self.set_object(params)
        return save_action, open_action

    def set_object(self,obj):
        from mirage.parameters import MicrolensingParameters, Parameters
        from functools import reduce
        from mirage.calculator.InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
        r_g = obj.quasar.r_g
        theta_E = obj.theta_E
        self.vDispersionInput.setValue(obj.lens.velocity_dispersion.to('km/s').value)
        self.lRedshiftInput.setValue(obj.lens.redshift)
        self.ellipRInput.setValue(obj.lens.ellipticity.magnitude.value)
        self.ellipThetaInput.setValue(obj.lens.ellipticity.direction.to('degree').value)
        self.shearRInput.setValue(obj.lens.shear.magnitude.value)
        self.shearThetaInput.setValue(obj.lens.shear.direction.to('degree').value)
        self.qRedshiftInput.setValue(obj.quasar.redshift)
        self.qMassInput.setValue(obj.quasar.mass.to('solMass').value)
        self.qRadiusInput.setValue(obj.quasar.radius.to(r_g).value)
        self.qRadiusUnit.setCurrentIndex(0)
        srt = math.sqrt(obj.ray_region.resolution.x.value*obj.ray_region.resolution.y.value)
        self.rootRayInput.setValue(int(srt))
        if isinstance(obj,MicrolensingParameters):
            self.enableMicrolensing.setChecked(True)
            minAxis = obj.source_plane.dimensions
            minAxis = min(minAxis.x.to(theta_E).value,minAxis.y.to(theta_E).value)
            self.sPlaneDimInput.setValue(int(minAxis))
            self.pcntStarsInput.setValue(float(obj.percent_stars))
            self.imfSeedInput.setValue(obj.star_generator.seed)
            if isinstance(obj.star_generator.IMF,Kroupa_2001):
                self.imfInput.setCurrentIndex(0)
            elif isinstance(obj.star_generator.IMF,Kroupa_2001_Modified):
                self.imfInput.setCurrentIndex(1)
            else:
                self.imfInput.setCurrentIndex(3)
            powers = obj.star_generator.IMF.powers
            breaks = obj.star_generator.IMF.mass_limits
            powerString = reduce(lambda acc,s: acc + " %.1f" % s,powers,"")[1:]
            breakString = reduce(lambda acc,s: acc + " %.1f" %s,breaks,"")[1:]
            self.imfAgingInput.setText("")
            self.imfPowersInput.setText(powerString)
            self.imfStepsInput.setText(breakString)
            try:
                conversions = obj.star_generator.IMF.conversions
                convString = reduce(lambda acc, s: acc + "%.1f:%.1f" % (s[0],s[1]), conversions)
                self.imfAgingInput.setText(convString)
            except:
                pass

        else:
            self.enableMicrolensing.setChecked(False)


    #TODO: Set up the set_object method.



class SimulationWidget(UserInputWidget):
    """docstring for SimulationWidget"""
    def __init__(self,parameters_widget):
        UserInputWidget.__init__(self)
        self._parameters_widget = parameters_widget
        self._parameters_widget.enableMicrolensing.setChecked(True)
        self._parameters_widget.enableMicrolensing.setEnabled(False)
        from random import randint
        self.lcRandSeed.clicked.connect(
            lambda : self.lcSeed.setValue(randint(1,999999999)))

    @property
    def qml(self):
        return "simulationview.ui"

    def close(self):
        self._parameters_widget.enableMicrolensing.setEnabled(True)

    def get_object(self,*args,**kwargs):
        from mirage.parameters import Simulation, ParametersError
        from mirage.util import Vec2D
        parameters = self._parameters_widget.get_object()
        if parameters:
            name = self.nameInput.text()
            desc = self.descriptionInput.toPlainText()
            tVar = self.varianceInput.toPlainText()
            trial_count = self.trialCountInput.value()
            special_parameters = []
            if self.mkMagMap.isChecked():
                # Making a magmap
                from mirage.parameters import MagnificationMapParameters
                mmRes = self.mmResolutionInput.value()
                mmRes = Vec2D(mmRes,mmRes)
                mm = MagnificationMapParameters(mmRes)
                special_parameters.append(mm)
            if self.mkLightCurves.isChecked():
                # Making light curves
                from mirage.parameters import LightCurvesParameters
                lcCount = self.lcCountInput.value()
                lcResolution = self.lcResolutionInput.value()
                lcResUnit = UserInputWidget.unitFromString(self.lcResolutionUnit.currentText()[2:],
                    parameters.quasar.r_g, parameters.theta_E)
                lcResolution = lcResolution/lcResUnit
                lcSeed = self.lcSeed.value()
                lcp = LightCurvesParameters(lcCount,lcResolution,lcSeed)
                special_parameters.append(lcp)
            sim = Simulation(parameters,name,desc,trial_count,tVar)
            for sp in special_parameters:
                sim.add_result(sp)
            try:
                #This varifies that the trial variance code is valid code.
                i = 0
                for i in range(sim.num_trials):
                    sim.set_trial(i)
                    sim.parameters
                return sim
            except ParametersError as e:
                UserInputWidget.warn_user("Error raised trying to produce parameters for trial %d." % i)
            except SyntaxError as e:
                UserInputWidget.warn_user("Trial Variance Input was not valid Python.")
            except:
                UserInputWidget.warn_user("Unknown error encountered in trial variance input. Please validate and try again.")
            return None

    def set_object(self,obj):
        self._parameters_widget.set_object(obj.parameters)
        self.nameInput.setText(obj.name)
        self.descriptionInput.setPlainText(obj.description)
        self.varianceInput.setPlainText(obj.trial_variance)
        if 'magmap' in obj:
            self.mkMagMap.setChecked(True)
            self.mmResolutionInput.setValue(int(obj['magmap'].resolution.x.value))
        if 'lightcurves' in obj:
            self.mkLightCurves.setChecked(True)
            self.lcCountInput.setValue(obj['lightcurves'].num_curves)
            self.lcSeed.setValue(obj['lightcurves'].seed)
            self.lcResolutionInput.setValue(obj['lightcurves'].sample_density.to('1/uas').value)

    def actionTriggers(self):
        def save_action():
            obj = self.get_object()
            if obj != None:
                from mirage.io import SimulationFileManager
                fm = SimulationFileManager()
                filename = QFileDialog.getSaveFileName(filter='*'+fm.extension)[0]
                if filename:
                    fm.open(filename)
                    fm.write(obj)
                    print("%s saved." + filename)
                    fm.close()
        def load_action():
            from mirage.lens_analysis import load_simulation
            filename = QFileDialog.getOpenFileName(filter='*')[0]#'*.param, *.sim, *.res, *.mp')[0]
            if filename:
                sim = load_simulation(filename)
                self.set_object(sim)
        return save_action, load_action

