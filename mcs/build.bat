docker buildx build --secret id=rcon_password,src=password.txt --build-arg version=1.21.1 --build-arg server_dir=./server -t mcs .