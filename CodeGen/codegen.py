# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 09:43:18 2019

@author: Nitzsche
"""
import io,sys,os
from PyQt5.QtWidgets import QMessageBox


#from globalThings import nuRDataTypes, nuRPlatforms
import globalThings as G

#markers to add project specific code into templates
marker1='/*nuRay: Add variable list for reading here*/'

class nuRCodeGenerator(object):
    indent='  '
    @classmethod
    def genCode(cls,d,params,signals,platform='Arduino Serial'):
        
        #check, whether myDir evironment Variable is set
        #if not os.getenv(nuRDir):
        if False:
            buttonReply = QMessageBox.information(None,
                                   'Code Gen',
                                   'Please set evironment variable '+nuRDir+' to the install directory, where the folder CodeTemplates is located!',
                                   QMessageBox.Ok)
        else:
            print('Generating Code in '+d)
            cls.gen_headers(d,params,signals)
            cls.gen_code_from_template(d,params,signals,platform)
        
        
    @classmethod
    def gen_code_from_template(cls,d,params,signals,platform):
        #open target nuRay.c and template, copy line by line and make the project specific additions
        with io.open(d+'\\nuRay.c','w') as c, io.open(G.nuRDir+'\\CodeGen\\CodeTemplates\\'+G.nuRPlatforms[platform]['code_template'],'r') as t:
            for line in t:
                if line.find(marker1)>-1:
                    mpos = line.find(marker1)
                    num=100 #index of first user parameter, 0--99 reserved for nuRay
                    for p in params:
                        c.write(mpos*' '+'case '+str(num)+':\n')
                        c.write(mpos*' '+cls.indent+'p=(byte*)&(nuR_ptr_params_write->'+p.name+');\n')
                        c.write(mpos*' '+cls.indent+'len='+str(G.nuRDataTypes[p.dataType]['len'])+';break;')
                        num+=1
                else:
                    c.write(line)


    @classmethod
    def gen_headers(cls,d,params,signals):         

        #interface/user header
        with io.open(d+'\\nuRay.h','w') as h:
            
            h.write('#ifndef __MRAY_HEADER_FILE_GENERATED_BY_MRAY\n')
            h.write('#define __MRAY_HEADER_FILE_GENERATED_BY_MRAY\n\n\n')
                    
            h.write('/*convienence access to params and signals*/\n')
            for p in params:
                h.write('#define '+p.name+' (nuR_ptr_params->'+p.name+')\n')
            h.write('\n')
            for p in signals:
                h.write('#define '+p.name+' (nuR_ptr_signals->'+p.name+')\n')
                    
            h.write('\n\n')
            h.write('int nuR_init(void)\n')
            h.write('int nuR_communicate(void)\n')
            h.write('extern params_struct_type *nuR_ptr_params;\n')
            h.write('extern signals_struct_type *nuR_ptr_signals;\n')
            h.write('\n\n#endif\n')
            
        #private/intern header
        with io.open(d+'\\nuRay_intern.h','w') as h:

            h.write('#ifndef __MRAY_INTERN_HEADER_FILE_GENERATED_BY_MRAY\n')
            h.write('#define __MRAY_INTERN_HEADER_FILE_GENERATED_BY_MRAY\n\n\n')

            h.write('/*structs for storing and sending parameters and signals*/\n')        
            h.write('typedef struct {\n')
            
            # sort by type
            #sort by descending number of bytes, so in C structs the long types do not fall on odd
            #addresses (on some platforms, a 4 byte number must be located on an address which is a multiple of 4)
            dts = list(G.nuRDataTypes.keys())
            dts.sort(key = lambda dt:G.nuRDataTypes[dt]['len'], reverse=True)
            for dt in dts:
                for p in (p for p in params if p.dataType==dt):
                    h.write(cls.indent+G.nuRDataTypes[dt]['ctype']+' '+p.name+';\n')
            h.write('} params_struct_type;\n\n')

            h.write('typedef struct {\n')

            for dt in dts:
                for p in (p for p in signals if p.dataType==dt):
                    h.write(cls.indent+G.nuRDataTypes[dt]['ctype']+' '+p.name+';\n')
            h.write('} signals_struct_type;\n\n')

            #s = [s for s in signals if s.dataType==dt]
            
            h.write('\n\n#endif\n')
        