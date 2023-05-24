# This script is written in Python (Jython implementation 2.5.3)
# See the Help menu for tutorials, example scripts and API
#   m_Mango_mango (class m_Mango) represents the application
#   m_VolMan_manager (class m_VolMan) represents this viewer
# Select a class in the API guide below to view its properties and methods

j_Object_result = m_VolMan_manager.runPlugin(
    "Extract Brain (BET)",["1","0.5","0.0","0.0","0.0","0.0","0.0"])
m_VolMan_manager.saveAs(
    m_VolMan_manager.makeFilename(".nii"),"NIFTI",2,2,True,False,0,287,0,287,
    0,169,0,0,0.8655263185501099,0.8655263185501099,1.0,1.0,"XYZ+++",False,
    False,False,False,1,False,False,False)
m_VolMan_manager.setMenuOption("Main Crosshairs",True)
m_VolMan_manager.setMenuOption("Lower Crosshairs",True)

#mango_extract\mango-script.bat -f mango_extract\mango_bet_winput.py D:\Data\testing\test_deface\test_deface.nii
##Que faire
##Requis: Avoir Mango installé si pas dans Program files, doit changer le path dans mango-script.bat
##copier le fichier dans un dossier tmp avant de deface