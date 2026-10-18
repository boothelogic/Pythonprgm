num1=float(input("Enter The First Number:"))
op=input("Enter The Operator:")
num2=float(input("Enter The Second Number:"))


if op=="+":
    print(num1 + num2)

elif op=="-":
    print(num1-num2)
    
elif op=="/":
    print(num1/num2)
    
elif op=="*":
    print(num1*num2)

else:
    print("SORRY! THE OPEATOR YOU HAVE USED IS NOT SUPPORTED BY THIS CALCULATOR !!")
    