checkpoint_dir=$1

first_path=$first_dir`ls -v "$checkpoint_dir"first_weights* | tail -1`
second_path=$second_dir`ls -v "$checkpoint_dir"second_weights* | tail -1`
belief_path=$belief_dir`ls -v "$checkpoint_dir"belief_weights* | tail -1`

echo $first_path
echo $second_path
echo $belief_path

mkdir -p most_recent_model

cp $first_path most_recent_model/first.ckpt
cp $second_path most_recent_model/second.ckpt
cp $belief_path most_recent_model/belief.ckpt
