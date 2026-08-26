# CSAW-Quals / pwn / unsafe-linking

You have found a mysterious notebook program running on a server. Unfortunately, the notebook program is faulty and has an issue with improperly handling memory allocation/deallocation. The notebook uses GLIBC-2.35 which implemented safelinking. Find a way to capture the flag by recovering leaked safelinking data!

`nc {box} {port}`
