from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import numpy as np

class BMS_experiment_result(models.Model):
    
    cathode=models.CharField(max_length=10,default="LFP",verbose_name="阳极")
    
    cathode_active_material=models.PositiveSmallIntegerField(default=11,verbose_name="阳极活性物质载量")
    
    anode=models.CharField(max_length=10,default="Li",verbose_name="阴极")
    
    li_metal_thickness=models.PositiveSmallIntegerField(default=180,verbose_name="锂金属厚度")
    
    charge_rate=models.CharField(max_length=10,default="0.5C",verbose_name="charge_rate")
    
    polymer=models.CharField(max_length=10,default="PBDT",verbose_name="聚合物")
    
    polymer_percentage=models.PositiveSmallIntegerField(default=15,verbose_name="聚合物在固态电解质中百分比")
    
    
    
    
    intristic_viscosity=models.PositiveSmallIntegerField(default=15)
    
    
    
    ionic_liquid=models.CharField(max_length=15,default="",verbose_name="离子液体")  
    
    
    
    ionic_liquid_electrolyte=models.CharField(max_length=25,default="",verbose_name="离子液体电解质")
    
    li_conc=models.DecimalField(max_digits=5,decimal_places=2,default=1.6)
    
    temperature=models.IntegerField(default=25)
    
    pressure=models.DecimalField(max_digits=5,decimal_places=2,default=0.7)
    
    
    thickness=models.PositiveIntegerField(default=100,verbose_name="膜的厚度")
    
    magnetic_field_direction=models.CharField(max_length=15,default="No",verbose_name="磁场方向")
    
    remark=models.CharField(max_length=15,default="default",verbose_name="Remarks",null=True,blank=True)
    
    
    bms_rawfile = models.FileField(upload_to='battery_manage_system/',verbose_name="BMS实验源文件",validators=[FileExtensionValidator(['csv','txt','xlsx'])],
                                    null=False,blank=False)
    
