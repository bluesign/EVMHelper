import json
import sys

typeMap = {
    "bytes32": "EVM.Bytes32",
    "bytes4": "EVM.Bytes4",
    "bytes": "EVM.Bytes",

    "string": "String",
    "bool": "Bool",
    "uint": "UInt",
    "uint8": "UInt8",
    "uint16": "UInt16",
    "uint32": "UInt32",
    "uint64": "UInt64",
    "uint128": "UInt128",
    "uint256": "UInt256",
    "int": "Int",
    "int8": "Int8",
    "int16": "Int16",
    "int32": "Int32",
    "int64": "Int64",
    "int128": "Int128",
    "int256": "Int256",
    "address": "EVM.EVMAddress",
}

def mapType(t):
    if t.endswith("[]"):
        inner = t[:len(t)-2]
        return "[" + mapType(inner) + "]"
    return typeMap[t]

class AbiFunction:

    def __init__(self, function):
        self.function = function
        self.name = function["name"]
        self.inputs = function["inputs"]
        self.isPayable = "stateMutability" in function and function["stateMutability"]=="payable"
        self.outputs = function["outputs"]
        self.selector = self.functionSelector()
        self.outputType = self.outputs[0]['type'] if len(self.outputs)>0 else None
        self.cadenceOutputType = mapType(self.outputType) if self.outputType else None
        self.type = function["type"]

    def sanitizeFunctionArgName(self, name):
        if name == "":
            return "arg"
        if name[0] == "_":
            return self.sanitizeFunctionArgName(name[1:])
        return name

    def functionSelector(self):
        types = [i["type"] for i in self.inputs]
        return f"{self.name}({','.join(types)})"

    def cadenceFunctionSignature(self) -> (str, str, bool):
        args = [f"{self.sanitizeFunctionArgName(i['name'])}: {mapType(i['type'])}" for i in self.inputs]
        if self.isPayable:
            args.append("value: UInt256")

        args = ", ".join(args)

        output = ""
        if self.cadenceOutputType:
            output = f": {self.cadenceOutputType}?"
        return (
            f"access(EVM.Owner) fun {self.name}({args}){output}",
            self.cadenceOutputType,
        )

    def cadenceFunction(self):
        signature, returnType = self.cadenceFunctionSignature()
        value = "nil"
        if self.isPayable:
            value = "value"

        cadenceReturnTypes = ",".join(
            [f"Type<{mapType(i['type'])}>()" for i in self.outputs]
        )

        inputNames = [self.sanitizeFunctionArgName(i['name']) for i in function['inputs']]
        if len(inputNames) > 0:
            inputs = f"[{', '.join(inputNames)}]"
        else:
            inputs = "nil"

        if self.cadenceOutputType:
            return f"\t{signature} {{ \n\t\treturn self.call(\"{self.selector}\", [{cadenceReturnTypes}], {inputs}, {value}) as? {returnType}\n\t}}\n"
        else:
            return f"\t{signature} {{ \n\t\tself.call(\"{self.selector}\", [{cadenceReturnTypes}], {inputs}, {value})\n\t}}\n"


if len(sys.argv) != 3:
    print("Usage: python abi.py <abi.json> <name> [defaultAddress]")
    sys.exit(1)

contractName = sys.argv[2]
defaultAddress = f"EVM.addressFromString({sys.argv[3]})" if len(sys.argv) == 4 else "base.address()"

abi = json.loads(open(sys.argv[1]).read())

functions  = ""
for function in abi:
    # only process functions
    if function["type"] != "function":
        continue
    functions = f"{functions}{AbiFunction(function).cadenceFunction()}"

print("""   access(all) attachment %s for EVM.CadenceOwnedAccount {
        access(EVM.Owner) var contractAddress: EVM.EVMAddress
        access(EVM.Owner) var gasLimit: UInt64

        access(EVM.Owner) fun call(
          _ signature:String, 
          _ returnTypes: [Type], 
          _ data:[AnyStruct]?,
          _ value: UInt256?
        ): AnyStruct{
        
          var data = EVM.encodeABIWithSignature(signature, data ??  [] as [AnyStruct])
          var lastResult = base.call(
            to: self.contractAddress,
            data: data,
            gasLimit: self.gasLimit,
            value: EVM.Balance(attoflow:value)
          )
          
          if lastResult!.status != EVM.Status.successful{
            return nil
          }
          
          var res = EVM.decodeABI(types: returnTypes, data: lastResult!.data)
          
          if res.length==1{
            return res[0]
          }
          return res
        }
        
        access(EVM.Owner) fun setContractAddress(_ contractAddress: EVM.EVMAddress){
          self.contractAddress = contractAddress    
        }
        
        access(EVM.Owner) fun setGasLimit(_ gasLimit: UInt64){
          self.contractAddress = contractAddress    
        }
        
        init(){
          self.contractAddress = %s
          self.gasLimit = 15_000_000
        }
    
// Generated functions
%s
    
    }""" % (contractName, defaultAddress, functions))
