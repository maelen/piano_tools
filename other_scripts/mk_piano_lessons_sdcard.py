#!/usr/bin/env python3

import shutil, os

try:
    shutil.rmtree('MUSICDAT')
except FileNotFoundError:
    pass
    
directories = [x for x in os.listdir() if os.path.isdir(x)]
directories.sort()
print(directories)

os.mkdir('MUSICDAT')
for i,directory in enumerate(directories):
        files2 = [f for f in os.listdir(directory) if f.endswith('.mid')]
        for j,file_tmp in enumerate(files2):
            print(directory+"/"+str(i)+file_tmp)
            shutil.copy(directory+"/"+file_tmp, 'MUSICDAT/'+str(i)+file_tmp)
        print(f"Range:{100*i+j} {100*(i+1)}")
        for k in range(100*i+j+2,100*(i+1)+1):
            new_filename=f'{k:03}_empty.mid'
            os.mknod(f'MUSICDAT/{new_filename}')
