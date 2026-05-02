#include <libsnark/common/default_types/r1cs_gg_ppzksnark_pp.hpp>
#include <libsnark/zk_proof_systems/ppzksnark/r1cs_gg_ppzksnark/r1cs_gg_ppzksnark.hpp>
#include <fstream>
#include "common.hpp"

using namespace libsnark;
using namespace std;

int main()
{
    //构造面包板
    protoboard<FieldT> pb = build_protoboard(NULL);
    const r1cs_constraint_system<FieldT> constraint_system = pb.get_constraint_system();
    //加载验证密钥
    fstream f_vk("vk.raw", ios_base::in);
    r1cs_gg_ppzksnark_verification_key<default_r1cs_gg_ppzksnark_pp> vk;
    f_vk >> vk;
    f_vk.close();
    //加载银行生成的证明
    fstream f_proof("proof.raw", ios_base::in);
    r1cs_gg_ppzksnark_proof<default_r1cs_gg_ppzksnark_pp> proof;
    f_proof >> proof;
    f_proof.close();
    //进行验证
    bool verified =
        r1cs_gg_ppzksnark_verifier_strong_IC<default_r1cs_gg_ppzksnark_pp>(vk, pb.primary_input(), proof);

    cout << "Number of R1CS constraints: " << constraint_system.num_constraints() << endl;
    cout << "Public input: " << pb.primary_input() << endl;
    cout << "Verification result: " << verified << endl;

    return 0;
}
