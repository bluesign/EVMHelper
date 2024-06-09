import "EVM"

access(all) contract EVMHelper{

  access(all) attachment ERC20 for EVM.CadenceOwnedAccount{
    access(EVM.Owner) var lastResult : EVM.Result?
    access(EVM.Owner) var contractAddress: EVM.EVMAddress?

    access(EVM.Owner) fun setContractAddress(_ contractAddress: EVM.EVMAddress){
        self.contractAddress = contractAddress    
    }

    access(EVM.Owner) fun call(_ signature:String, _ returnTypes: [Type], _ data:[AnyStruct]?): AnyStruct{
      
      var data = EVM.encodeABIWithSignature(signature, data ??  [] as [AnyStruct])
      self.lastResult = base.call(
        to: self.contractAddress ?? base.address(),
        data: data,
        gasLimit: 15000000,
        value: EVM.Balance(attoflow:0)
      )
      
      if self.lastResult!.status != EVM.Status.successful{
        return nil
      }
      
      var res = EVM.decodeABI(types: returnTypes, data: self.lastResult!.data)
      
      if res.length==1{
        return res[0]
      }

      return res

    }


    access(EVM.Owner) fun name():String? {
      return self.call("name()", [Type<String>()], nil) as? String
    }

    access(EVM.Owner) fun symbol():String? {
      return self.call("symbol()", [Type<String>()], nil) as? String
    }

    access(EVM.Owner) fun decimals():UInt8? {
      return self.call("decimals()", [Type<UInt8>()], nil) as? UInt8
    }

    access(EVM.Owner) fun totalSupply():UInt256? {
      return self.call("totalSupply()", [Type<UInt256>()], nil) as? UInt256
    }

    access(EVM.Owner) fun balanceOf(address:EVM.EVMAddress):UInt256? {
      return self.call("balanceOf(address)", [Type<UInt256>()], [address]) as? UInt256
    }

    access(EVM.Owner) fun transfer(to:EVM.EVMAddress, value:UInt256): Bool? {
        return self.call("transfer(address,uint256)", [Type<Bool>()], [to, value]) as? Bool
    }

    access(EVM.Owner) fun allowance(owner:EVM.EVMAddress, spender:EVM.EVMAddress): UInt256? {
        return self.call("allowance(address,address)", [Type<UInt256>()], [owner, spender]) as? UInt256
    }
 
    access(EVM.Owner) fun approve(spender:EVM.EVMAddress, value:UInt256): Bool? {
        return self.call("approve(address,uint256)", [Type<Bool>()], [spender, value]) as? Bool
    }

    access(EVM.Owner) fun transferFrom(from:EVM.EVMAddress, to:EVM.EVMAddress, value:UInt256): Bool? {
        return self.call("transferFrom(address,address,uint256)", [Type<Bool>()], [from, to, value]) as? Bool
    }

    init(){
      self.lastResult = nil
      self.contractAddress = nil
    }

  }

}
