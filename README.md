# FaceRecognition_AS_a_service
Open source face recognition to name as a service

Will update the Readme shortly.

The services uses some tips and tricks from pyimagesearch. Relies on Dlib , flask , rabbitmq and mysql.


Aug-rest Is the micro service for uploading and searching and many more . swagger will help you understand what it does.


AugQ are queues:
  [-] SC and SG mean Search via CPU or search via GPU .
  [-] TC and TG mean Train the images via CPU or GPU
  [-] AugQ-upload is which handles which images goto which queue
  [-] AugQ-misc updates an image status.
  
  
This project can be used to aid in finding missing people by crowd sourcing. you can apply this to many other things.


Enjoy
