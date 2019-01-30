
import observing

"""
 Assumes the telescopes have been point to where you what, i.e. the telescope
  will not be asked to slew. And no real exposures will be taken, will just 
  print to screen what the exposure should be.
  
 Assume the observing recipe is called <target_name>.obs
 
 18/1/19 - this is not tested yet
  
 
"""

target_name = 'test_target_single_Texp'
target_coords = ['10:46:04','-46:08:06']
target_type = 'TEST'

def main():
	
	observing.basic_exposure(target_name,target_coords,target_type)

if __name__ == '__main__':
	main()