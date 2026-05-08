

from django.contrib.sitemaps import Sitemap              
from django.urls import reverse                          

class StaticViewSitemap(Sitemap):                        
    changefreq = "weekly"                                
    priority = 0.8                                       
    protocol = "https"                                       
    
    def items(self):                                     
        return [
            'home:homepage',                                      
            'autocompute:index',                               
            'ionic_liquid:ionic_liquid_base',                             
            'polymer:display',                                  
            'crystals:crystal_display',                                   
            'bms:battery_manage_system',                                       
            
            'home:tutorial_list',                           
            'home:how_to_cite',                              
            
        ]

    def location(self, item):                            
        return reverse(item)